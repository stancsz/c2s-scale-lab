# C2S-Scale Medical Research Lab — Research Statement

Purpose
- This repository is maintained by the C2S-Scale Medical Research Lab to provide reproducible tooling and experiments for evaluating large language models (LLMs) in biomedical research tasks. It focuses on safe, auditable model runs, embedding-based evaluation, and clear provenance for models and data.

Responsible use & safety
- Do not use LLM outputs as definitive clinical advice. All model outputs must be reviewed by qualified personnel before any application in real-world medical contexts.
- Avoid prompts that ask for procedural wet-lab protocols, clinical diagnoses, or patient-specific recommendations. Use high-level conceptual prompts and simulations only.
- Track and document sensitive inputs, and avoid including protected health information (PHI) in experiment prompt files or stored outputs.

Model licensing & weights
- Respect model licenses. Do not redistribute weights that are restricted by the upstream license.
- When using Hugging Face models, record the model name, revision (commit or tag), and license in experiment metadata.
- For local deployment (e.g., Ollama or converted formats), document conversion steps and source references; do not host or share converted weights if licensing forbids redistribution.

Reproducibility & provenance
- Record environment (Python version, pip freeze / requirements.txt, Dockerfile), model source (HF repo + revision), and exact prompt files.
- Store experiment outputs under experiments/outputs with timestamped filenames and a simple metadata sidecar (JSON) including model, mode, commit SHA, and environment info.

CI, secrets, and safe automation
- CI workflows may run experiments only when appropriate secrets are available (e.g., HF_TOKEN). Do not commit tokens or other secrets to source control.
- Use GitHub Actions secrets and restrict access to repositories appropriately.

How to run experiments (high-level)
- Follow README.md for environment setup (venv or Docker).
- Use run_experiment.py for unified runs across modes: hf, ollama, local.
- Save outputs with experiments/run_and_save.sh or the run_experiment.py save option for downstream embedding-based eval.

Contact, authorship, and attribution
- Record principal investigators and maintainers in the repository metadata (e.g., AUTHORS or in the project README).
- When publishing results, attribute upstream model creators and cite model licenses appropriately.

Next steps
- Add CODE_OF_CONDUCT.md, AUTHORS, and an explicit CONTRIBUTING guide tailored to safe biomedical LLM experiments.
- Add automated metadata capture in the experiment runner to write JSON sidecars alongside outputs.
