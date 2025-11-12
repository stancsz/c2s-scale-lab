#!/usr/bin/env python3
"""
extract_evidence.py

Lightweight evidence extractor that ingests ClinicalTrials.gov study fields JSON and
PubMed article JSON (as produced by collect_trials.py and collect_pubmed.py) and
produces a structured JSON file of candidate evidence entries.

This script uses simple heuristics (field mapping + regex) to extract:
 - intervention
 - population
 - outcome snippets
 - sample size (when available)
 - provenance (source, id, url-like fields)

Safety: Outputs are informational only and must NOT be interpreted as clinical advice.
Human curation is required before any downstream use.

Example:
  python experiments/extract_evidence.py --trials experiments/outputs/trials.json \\
    --pubmed experiments/outputs/pubmed.json \\
    --out experiments/outputs/structured_evidence.json
"""

import argparse
import json
import os
import re
from collections import Counter
from typing import List, Dict, Any

SAMPLE_REGEX = re.compile(r"(?P<n>\b\d{1,5}\b)\s+(?:participants|subjects|people|patients|volunteers)", flags=re.I)
OUTCOME_REGEX = re.compile(r"(primary outcome[s]?:|primary endpoint[s]?:|secondary outcome[s]?:|secondary endpoint[s]?:|outcome measures?:)", flags=re.I)

def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)

def extract_from_trial(trial: Dict[str, Any]) -> Dict[str, Any]:
    # trial fields from ClinicalTrials.gov StudyFieldsResponse entries are lists per field
    def first(field):
        if isinstance(field, list):
            return field[0] if field else None
        return field

    nct_id = first(trial.get("NCTId"))
    title = first(trial.get("BriefTitle")) or first(trial.get("OfficialTitle"))
    interventions = trial.get("InterventionName") or []
    intervention = interventions[0] if interventions else None
    condition = (trial.get("Condition") or [])
    condition_txt = "; ".join(condition) if condition else None
    status = first(trial.get("OverallStatus"))
    study_type = first(trial.get("StudyType"))
    phase = first(trial.get("Phase"))
    enrollment = first(trial.get("EnrollmentCount"))
    start = first(trial.get("StartDate"))
    completion = first(trial.get("CompletionDate"))
    country = first(trial.get("LocationCountry"))

    # attempt to find sample size from enrollment or title text
    sample_size = None
    if enrollment:
        try:
            sample_size = int(enrollment)
        except Exception:
            sample_size = None
    if not sample_size and title:
        m = SAMPLE_REGEX.search(title)
        if m:
            sample_size = int(m.group("n"))

    # outcomes: ClinicalTrials.gov StudyFields API may not include outcome text; fallback to title
    outcome_snippet = None
    # Try to find explicit outcome-like strings in official title
    if title:
        m = OUTCOME_REGEX.search(title)
        if m:
            outcome_snippet = title

    entry = {
        "source": "clinicaltrials.gov",
        "id": nct_id,
        "title": title,
        "intervention": intervention,
        "condition": condition_txt,
        "status": status,
        "study_type": study_type,
        "phase": phase,
        "sample_size": sample_size,
        "start_date": start,
        "completion_date": completion,
        "location_country": country,
        "outcome_snippet": outcome_snippet,
        "raw": trial
    }
    return entry

def extract_from_pubmed(article: Dict[str, Any]) -> Dict[str, Any]:
    pmid = article.get("pmid")
    title = article.get("title")
    abstract = article.get("abstract") or ""
    doi = article.get("doi")
    # Try to find sample sizes in abstract
    sample_size = None
    m = SAMPLE_REGEX.search(abstract)
    if m:
        try:
            sample_size = int(m.group("n"))
        except Exception:
            sample_size = None

    # Attempt to find likely intervention phrases by simple heuristic: look for words like "supplement", "drug", "senolytic", "metformin", "diet", "exercise"
    keywords = ["supplement", "drug", "senolytic", "metformin", "rapamycin", "diet", "exercise", "caloric", "fasting", "resveratrol", "nicotinamide", "NAD", "senescence"]
    found = []
    lower_text = (title or "") + "\n" + abstract.lower()
    for kw in keywords:
        if kw.lower() in lower_text:
            found.append(kw)
    intervention = ", ".join(found) if found else None

    # outcome snippet: first 200 chars of abstract
    outcome_snippet = abstract[:500] if abstract else None

    entry = {
        "source": "pubmed",
        "id": pmid,
        "title": title,
        "doi": doi,
        "intervention": intervention,
        "sample_size": sample_size,
        "outcome_snippet": outcome_snippet,
        "raw": article
    }
    return entry

def merge_evidence(trials_entries: List[Dict[str, Any]], pubmed_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    evidence = []
    # Add trials first
    for t in trials_entries:
        evidence.append(extract_from_trial(t))
    # Add pubmed
    for p in pubmed_entries:
        evidence.append(extract_from_pubmed(p))
    return evidence

def top_interventions(evidence: List[Dict[str, Any]], top_n=20):
    c = Counter()
    for e in evidence:
        intr = e.get("intervention")
        if isinstance(intr, str):
            # split comma-separated heuristics
            for part in [s.strip() for s in intr.split(",")]:
                if part:
                    c[part.lower()] += 1
    return c.most_common(top_n)

def main():
    parser = argparse.ArgumentParser(description="Extract structured evidence from trials and PubMed outputs.")
    parser.add_argument("--trials", type=str, default=None, help="Path to trials JSON (from collect_trials.py)")
    parser.add_argument("--pubmed", type=str, default=None, help="Path to pubmed JSON (from collect_pubmed.py)")
    parser.add_argument("--out", type=str, default="experiments/outputs/structured_evidence.json", help="Output JSON path")
    args = parser.parse_args()

    trials_data = {"studies": []}
    pubmed_data = {"articles": []}

    if args.trials and os.path.exists(args.trials):
        trials_data = load_json(args.trials)
    if args.pubmed and os.path.exists(args.pubmed):
        pubmed_data = load_json(args.pubmed)

    trials = trials_data.get("studies", [])
    articles = pubmed_data.get("articles", [])

    evidence = merge_evidence(trials, articles)

    summary = {
        "provenance": {
            "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
            "trials_input_count": len(trials),
            "pubmed_input_count": len(articles),
        },
        "top_interventions": top_interventions(evidence, top_n=50),
        "evidence": evidence
    }

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)

    print(f"Wrote structured evidence ({len(evidence)} entries) to {args.out}")

if __name__ == "__main__":
    main()
