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
