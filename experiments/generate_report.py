#!/usr/bin/env python3
"""
generate_report.py

Create a human-readable Markdown report from structured evidence JSON.
- Loads structured evidence (expected from extract_evidence.py).
- Optionally calls experiments/generate_llm_summary.py if available to produce
  model-draft synthesis paragraphs. If the LLM helper is unavailable, produces
  deterministic, non-actionable summaries.
- Renders experiments/report_template.md by filling named placeholders if present,
  otherwise appends sections in a sensible order.
- Writes output to experiments/outputs/final_report.md and prints the path.

Safety: All outputs are informational only and labelled. Do NOT use outputs as
clinical guidance. Manual curation and verification required.
"""
from __future__ import annotations

import argparse
import json
import sys
import textwrap
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE = Path(__file__).resolve().parent
DEFAULT_EVIDENCE = BASE / "outputs" / "structured_evidence.json"
DEFAULT_TEMPLATE = BASE / "report_template.md"
DEFAULT_OUTDIR = BASE / "outputs"
DEFAULT_OUT = DEFAULT_OUTDIR / "final_report.md"


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def extract_entries(evidence: Any) -> List[Dict]:
    # Accept either a dict with "entries" or a raw list
    if isinstance(evidence, dict):
        if "entries" in evidence and isinstance(evidence["entries"], list):
            return evidence["entries"]
        # other common shape: {"evidence": [...]}
        for key in ("evidence", "items", "results"):
            if key in evidence and isinstance(evidence[key], list):
                return evidence[key]
        # fallback: attempt to interpret dict values that look like list of dicts
        vals = [v for v in evidence.values() if isinstance(v, list)]
        for v in vals:
            if all(isinstance(i, dict) for i in v):
                return v
        return []
    elif isinstance(evidence, list):
        return evidence
    else:
        return []


def guess_interventions_from_entry(entry: Dict) -> List[str]:
    candidates = []
    # common keys to check
    keys = [
        "intervention",
        "interventions",
        "intervention_name",
        "interventionNames",
        "intervention_names",
        "treatment",
        "treatments",
        "name",
        "names",
    ]
    for k in keys:
        if k in entry:
            v = entry[k]
            if isinstance(v, str):
                candidates.append(v.strip())
            elif isinstance(v, list):
                candidates.extend([str(x).strip() for x in v if x])
    # also scan free-text fields for likely intervention keywords
    for k in ("summary", "outcome_snippet", "abstract", "description", "title"):
        if k in entry and isinstance(entry[k], str):
            text = entry[k]
            # naive: split on semicolon/commas and pick short phrases with keywords
            for part in text.split(";"):
                p = part.strip()
                if not p:
                    continue
                lowered = p.lower()
                if any(tok in lowered for tok in ("metformin", "rapamycin", "senolytic", "diet", "exercise", "supplement", "resveratrol", "nicotinamide", "sirtuin", "caloric", "fasting", "exercise")):
                    candidates.append(p)
    # dedupe and return up to 5
    seen = []
    for c in candidates:
        if c and c not in seen:
            seen.append(c)
        if len(seen) >= 5:
            break
    return seen


def top_interventions(entries: List[Dict], top_n: int = 10) -> List[tuple]:
    counter = Counter()
    for e in entries:
        ints = guess_interventions_from_entry(e)
        for i in ints:
            counter[i] += 1
    return counter.most_common(top_n)


def build_report_text(
    entries: List[Dict],
    template_text: Optional[str],
    use_llm: bool = False,
    llm_callable=None,
    max_llm_tokens: int = 200,
) -> str:
    generated_at = datetime.now(timezone.utc).isoformat()
    n_entries = len(entries)
    top = top_interventions(entries, top_n=10)

    # Basic deterministic executive summary (non-actionable)
    exec_lines = [
        f"Report generated: {generated_at} (UTC)",
        "",
        "Safety disclaimer: This report is informational only. It is NOT clinical guidance. "
        "All model-generated text or automated summaries are labelled as model-drafts and "
        "require human review and verification of identifiers (DOI, NCT) and outcome measures.",
        "",
        f"Number of evidence items processed: {n_entries}",
    ]
    if top:
        exec_lines.append("")
        exec_lines.append("Top interventions / topics (automatically extracted):")
        for name, count in top:
            exec_lines.append(f"- {name} — {count} source(s)")

    executive_summary = "\n".join(exec_lines)

    # Methods: describe pipeline and provenance heuristics
    methods = textwrap.dedent(
        """\
        Methods
        -------
        Data sources:
        - ClinicalTrials.gov Study Fields API (if used)
        - NCBI PubMed E-utilities (esearch + efetch) (if used)
        - Heuristic evidence extraction performed by experiments/extract_evidence.py
        - Optional LLM draft synthesis (labelled)

        Processing:
        - Entries were parsed from a structured JSON produced by extract_evidence.py.
        - Interventions/topics were heuristically extracted from known fields and short text snippets.
        - No clinical recommendations are produced by this script.
        """
    )

    # Results: include short enumerations and small sample
    results_lines = ["Results", "-------", f"Total entries: {n_entries}", ""]
    if top:
        results_lines.append("Top interventions (summary):")
        for name, count in top:
            results_lines.append(f"- **{name}** — {count} evidence item(s)")
        results_lines.append("")

    # include a small sample of evidence (first 5) with provenance
    results_lines.append("Sample evidence (first 5 items):")
    for i, e in enumerate(entries[:5], start=1):
        title = e.get("title") or e.get("BriefTitle") or e.get("brief_title") or e.get("name") or "<no title>"
        source = e.get("provenance") or e.get("source") or e.get("source_url") or e.get("nct_id") or e.get("pmid") or ""
        snippet = e.get("outcome_snippet") or e.get("abstract") or e.get("summary") or ""
        snippet = (snippet[:400] + "...") if snippet and len(snippet) > 400 else snippet
        results_lines.append(f"{i}. {title}")
        if source:
            results_lines.append(f"   - provenance: {source}")
        if snippet:
            results_lines.append(f"   - snippet: {snippet}")
        results_lines.append("")

    results = "\n".join(results_lines)

    # Model draft: if requested and callable, craft a prompt and call it
    model_draft_text = ""
    if use_llm and llm_callable is not None:
        prompt_lines = [
            "You are asked to produce a concise, non-actionable research synthesis summary.",
            "Label the output as a model-draft and avoid giving prescriptive or clinical advice.",
            "",
            "Context:",
            f"- Evidence items processed: {n_entries}",
            "- Top interventions (auto-extracted):",
        ]
        for name, count in top[:10]:
            prompt_lines.append(f"- {name} — {count} source(s)")
        prompt_lines.append("")
        prompt_lines.append("Produce a short executive-style paragraph (3-6 sentences) summarizing the landscape.")
        prompt = "\n".join(prompt_lines)

        try:
            # llm_callable should accept (prompt, max_tokens) or (prompt,) depending on implementation
            resp = None
            try:
                resp = llm_callable(prompt, max_new_tokens=max_llm_tokens)
            except TypeError:
                try:
                    resp = llm_callable(prompt, max_tokens=max_llm_tokens)
                except TypeError:
                    resp = llm_callable(prompt)
            if isinstance(resp, (list, tuple)):
                model_text = str(resp[0]) if resp else ""
            else:
                model_text = str(resp)
            model_draft_text = textwrap.dedent(
                f"""\
                Model-draft synthesis (automated and unreviewed)
                -----------------------------------------------
                {model_text.strip()}
                """
            )
        except Exception as exc:
            model_draft_text = textwrap.dedent(
                f"""\
                Model-draft synthesis (failed to call LLM)
                ------------------------------------------
                LLM call failed with error: {exc}
                A deterministic summary is provided instead.
                """
            )

    if not model_draft_text:
        # deterministic fallback paragraph
        top_names = ", ".join([n for n, _ in top[:5]]) or "no clear interventions"
        deterministic = (
            f"Automated (deterministic) summary: The collected evidence contains {n_entries} items. "
            f"Automatically extracted top topics include: {top_names}. Outputs are draft-level "
            "and require human review for interpretation, validation of identifiers, and to avoid "
            "clinical recommendations."
        )
        model_draft_text = textwrap.dedent(
            f"""\
            Model-draft synthesis (deterministic fallback)
            ---------------------------------------------
            {deterministic}
            """
        )

    # Limit appendix: include JSON provenance summary (counts by source type if available)
    appendix_lines = ["Appendix", "--------", "Provenance summary:"]
    # try simple counts by a "source" or "provenance" field
    src_counter = Counter()
    for e in entries:
        src = e.get("source") or e.get("provenance") or e.get("source_url") or e.get("nct_id") or e.get("pmid") or "unknown"
        if isinstance(src, list):
            src = src[0] if src else "unknown"
        src_counter[src] += 1
    for src, cnt in src_counter.most_common(10):
        appendix_lines.append(f"- {src}: {cnt}")
    appendix_lines.append("")
    appendix_lines.append("Full structured evidence is available in the JSON used to render this report.")
    appendix = "\n".join(appendix_lines)

    # Compose full report by filling template placeholders if present
    sections = {
        "{{EXECUTIVE_SUMMARY}}": executive_summary,
        "{{METHODS}}": methods,
        "{{RESULTS}}": results,
        "{{MODEL_DRAFT}}": model_draft_text,
        "{{APPENDIX}}": appendix,
    }

    if template_text:
        report_text = template_text
        for placeholder, body in sections.items():
            if placeholder in report_text:
                report_text = report_text.replace(placeholder, body)
        # if placeholders not present, append missing sections at end
        missing = [k for k in sections.keys() if k not in template_text]
        if missing:
            report_text = report_text.rstrip() + "\n\n" + "\n\n".join(sections.values())
    else:
        # Build a minimal report
        report_text = "\n\n".join(
            [
                "# Research Synthesis — Model Draft (Informational Only)",
                "## Executive summary",
                executive_summary,
                "## Methods",
                methods,
                "## Results",
                results,
                "## Model-draft synthesis",
                model_draft_text,
                "## Appendix",
                appendix,
            ]
        )

    # Add generation metadata footer
    footer = f"\n\n---\nReport generated by experiments/generate_report.py on {generated_at} (UTC)."
    report_text = report_text + footer
    return report_text


def try_load_llm_callable(module_path: Path):
    """
    Try returning a callable that accepts a prompt and returns text.
    It will attempt to import experiments/generate_llm_summary.py and locate a function.
    """
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location("gen_llm", str(module_path))
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore
            # heuristic: look for common function names
            for name in ("generate_summary", "generate", "run_llm", "create_summary", "main"):
                if hasattr(mod, name):
                    fn = getattr(mod, name)
                    if callable(fn):
                        return fn
            # fallback: if module exposes a pipeline function "generate_from_prompt"
            if hasattr(mod, "generate_from_prompt"):
                return getattr(mod, "generate_from_prompt")
    except Exception:
        return None
    return None


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Render a Markdown report from structured evidence JSON.")
    p.add_argument("--evidence", "-e", type=Path, default=DEFAULT_EVIDENCE, help="Path to structured_evidence.json")
    p.add_argument("--template", "-t", type=Path, default=DEFAULT_TEMPLATE, help="Path to report template (Markdown)")
    p.add_argument("--out", "-o", type=Path, default=DEFAULT_OUT, help="Output Markdown path")
    p.add_argument("--use-llm", action="store_true", help="Attempt to call local LLM summary helper (optional)")
    p.add_argument("--max-llm-tokens", type=int, default=200, help="Max tokens for LLM draft")
    args = p.parse_args(argv)

    if not args.evidence.exists():
        print(f"Error: evidence file not found: {args.evidence}", file=sys.stderr)
        return 2

    evidence_obj = load_json(args.evidence)
    entries = extract_entries(evidence_obj)

    template_text = args.template.read_text(encoding="utf-8") if args.template.exists() else None

    llm_callable = None
    if args.use_llm:
        llm_module_path = BASE / "generate_llm_summary.py"
        if llm_module_path.exists():
            llm_callable = try_load_llm_callable(llm_module_path)
            if llm_callable is None:
                print("Warning: found generate_llm_summary.py but could not locate a callable function inside it.", file=sys.stderr)
        else:
            print("Warning: --use-llm requested but experiments/generate_llm_summary.py not found; falling back to deterministic summary.", file=sys.stderr)

    report = build_report_text(entries, template_text, use_llm=args.use_llm, llm_callable=llm_callable, max_llm_tokens=args.max_llm_tokens)

    save_text(args.out, report)
    print(f"Wrote report: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
