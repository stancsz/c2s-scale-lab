# Research Report Template — LLM-assisted Evidence Synthesis

IMPORTANT NOTE (SAFETY)
This repository provides tools to collect publicly available metadata from ClinicalTrials.gov and PubMed and to generate summary reports for research purposes only. Outputs are informational and must NOT be interpreted as medical advice, treatment recommendations, or clinical protocols. Consult qualified clinicians and domain experts before acting on any material contained in generated reports.

---

## Title
[Short, descriptive title of the assembled evidence]

## Authors
- [List of authors / script + model + date]

## Executive Summary
- One-paragraph high-level summary of scope, key findings (non-prescriptive), and major caveats.

## Scope and Purpose
- Objective of the review
- Search terms / date range
- Inclusion/exclusion criteria (high-level)

## Data Sources
- ClinicalTrials.gov (study metadata)
- PubMed / MEDLINE (abstracts and metadata)
- Other public repositories (specify)

## Methods
- Data collection: brief description of scripts used
  ```bash
  # Example: fetch trials metadata
  python experiments/collect_trials.py --query "aging OR longevity" --max 200 --out experiments/outputs/trials.json
  # Example: fetch PubMed abstracts
  python experiments/collect_pubmed.py --query "aging interventions" --max 200 --out experiments/outputs/pubmed.json
  ```
- Evidence extraction: description of NLP extractor and fields produced (intervention, outcome, population, sample_size, conclusion_snippet)
- LLM summarization: prompt template and model used (non-clinical summary only)

## Results
- High-level aggregated tables (placeholders)
  - Number of trials retrieved
  - Number of PubMed records retrieved
  - Top interventions (by count)
- Representative structured evidence entries (short examples)
  ```json
  {
    "source": "clinicaltrials.gov",
    "nct_id": "NCT00000000",
    "intervention": "Example supplement",
    "population": "Adults aged 60+",
    "outcome_measures": ["primary outcome description"],
    "status": "Completed"
  }
  ```

## Synthesized Findings (LLM Draft)
- Non-prescriptive, high-level synthesis paragraphs produced by the LLM from structured evidence. Clearly label these as model-generated drafts requiring human review.

## Limitations
- Coverage limitations (API quotas, indexing, publication bias)
- Model limitations (small models may hallucinate; outputs must be verified)
- Ethical and safety considerations

## Recommendations for Human Curation
- Verify trial identifiers and DOIs manually
- Validate extracted outcome measures against original sources
- Consult domain experts before any translation to practice

## References
- List DOIs, PubMed IDs, and ClinicalTrials.gov URLs used in the report

## Appendix — Run Commands & Reproducibility
- Environment setup
  ```bash
  python -m venv .venv
  .venv/Scripts/activate    # Windows
  pip install -r requirements.txt
  ```
- Example end-to-end
  ```bash
  python experiments/collect_trials.py --query "senolytic OR senolytics" --max 100 --out experiments/outputs/trials_senolytic.json
  python experiments/collect_pubmed.py --query "senolytic trials" --max 200 --out experiments/outputs/pubmed_senolytic.json
  python experiments/extract_evidence.py --trials experiments/outputs/trials_senolytic.json --pubmed experiments/outputs/pubmed_senolytic.json --out experiments/outputs/structured_evidence.json
  python experiments/generate_report.py --evidence experiments/outputs/structured_evidence.json --template experiments/report_template.md --out experiments/outputs/final_report.md
  ```

## Contact / Provenance
- Scripts and model versions used
- Author / maintainer contact info

Report generated: 2025-11-12T05:54:45.458662+00:00 (UTC)

Safety disclaimer: This report is informational only. It is NOT clinical guidance. All model-generated text or automated summaries are labelled as model-drafts and require human review and verification of identifiers (DOI, NCT) and outcome measures.

Number of evidence items processed: 4

Top interventions / topics (automatically extracted):
- Metformin — 1 source(s)
- Metformin to test effects on markers of aging in older adults (Pilot study, 100 participants) — 1 source(s)
- Rapamycin — 1 source(s)
- Rapamycin and aging biomarkers in adults (50 participants) — 1 source(s)
- metformin — 1 source(s)
- Abstract: We randomized 120 older adults to metformin or placebo and measured inflammatory markers and function over 12 months. Results showed modest changes in markers but no adverse safety signals... — 1 source(s)
- Randomized trial of metformin in older adults: effects on inflammation and functional markers — 1 source(s)
- exercise — 1 source(s)
- Abstract: A 16-week supervised exercise program in 200 participants improved composite markers of healthspan including VO2max and insulin sensitivity... — 1 source(s)
- Exercise intervention improves composite healthspan markers in midlife adults — 1 source(s)

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


Results
-------
Total entries: 4

Top interventions (summary):
- **Metformin** — 1 evidence item(s)
- **Metformin to test effects on markers of aging in older adults (Pilot study, 100 participants)** — 1 evidence item(s)
- **Rapamycin** — 1 evidence item(s)
- **Rapamycin and aging biomarkers in adults (50 participants)** — 1 evidence item(s)
- **metformin** — 1 evidence item(s)
- **Abstract: We randomized 120 older adults to metformin or placebo and measured inflammatory markers and function over 12 months. Results showed modest changes in markers but no adverse safety signals...** — 1 evidence item(s)
- **Randomized trial of metformin in older adults: effects on inflammation and functional markers** — 1 evidence item(s)
- **exercise** — 1 evidence item(s)
- **Abstract: A 16-week supervised exercise program in 200 participants improved composite markers of healthspan including VO2max and insulin sensitivity...** — 1 evidence item(s)
- **Exercise intervention improves composite healthspan markers in midlife adults** — 1 evidence item(s)

Sample evidence (first 5 items):
1. Metformin to test effects on markers of aging in older adults (Pilot study, 100 participants)
   - provenance: clinicaltrials.gov

2. Rapamycin and aging biomarkers in adults (50 participants)
   - provenance: clinicaltrials.gov

3. Randomized trial of metformin in older adults: effects on inflammation and functional markers
   - provenance: pubmed
   - snippet: Abstract: We randomized 120 older adults to metformin or placebo and measured inflammatory markers and function over 12 months. Results showed modest changes in markers but no adverse safety signals...

4. Exercise intervention improves composite healthspan markers in midlife adults
   - provenance: pubmed
   - snippet: Abstract: A 16-week supervised exercise program in 200 participants improved composite markers of healthspan including VO2max and insulin sensitivity...


Model-draft synthesis (deterministic fallback)
---------------------------------------------
Automated (deterministic) summary: The collected evidence contains 4 items. Automatically extracted top topics include: Metformin, Metformin to test effects on markers of aging in older adults (Pilot study, 100 participants), Rapamycin, Rapamycin and aging biomarkers in adults (50 participants), metformin. Outputs are draft-level and require human review for interpretation, validation of identifiers, and to avoid clinical recommendations.


Appendix
--------
Provenance summary:
- clinicaltrials.gov: 2
- pubmed: 2

Full structured evidence is available in the JSON used to render this report.

---
Report generated by experiments/generate_report.py on 2025-11-12T05:54:45.458662+00:00 (UTC).