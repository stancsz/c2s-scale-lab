# C2S-Scale Medical Research Lab — reproducible LLM experiments for biomedical research

Goal
- This repository represents the "C2S-Scale Medical Research Lab": a reproducible, auditable set of experiments, tools, and CI for using large language models (LLMs) safely in biomedical research. It focuses on running and evaluating c2s-scale (Gemma) and compatible LLMs via Hugging Face, Ollama, or local Transformers.
- Provide clear, reproducible environment setup (venv, Docker), usage examples, and embedding-based evaluation pipelines while respecting model licensing and safety constraints.

Quick checklist
- [x] Analyze requirements and create docs
- [ ] Add example script (example.py)
- [ ] Add setup scripts (scripts/setup.sh, scripts/setup.ps1)
- [ ] Add Dockerfile and docker-compose example
- [ ] Add CI workflow for reproducible tests
- [ ] Verify end-to-end run locally
- [ ] Publish reproduction steps in a single script

Reproducible installation (recommended)

1) Clone repo
```bash
git clone https://github.com/stancsz/c2s-scale-longevity-experiment.git
cd c2s-scale-longevity-experiment
```

2) Python virtualenv + pip (recommended)
```bash
# Unix / WSL / Git Bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
# install from PyPI if available
pip install c2s-scale
# OR if you have source in this repo:
# pip install -e .
```

Windows (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install c2s-scale
```

3) Example usage (CLI)
```bash
# Common pattern if c2s-scale provides a CLI
c2s-scale --help
c2s-scale run --config path/to/config.yaml
```

4) Example usage (Python)
```python
# python
# NOTE: adjust the import/API to match the package's real API
from c2s_scale import Client

client = Client()          # instantiate client (example)
result = client.run("experiment-config.yaml")
print(result)
```

Docker (fully reproducible)
- Docker isolates system-level differences. Example Dockerfile:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "example.py"]
```
Example build & run:
```bash
docker build -t c2s-scale-example:latest .
docker run --rm c2s-scale-example:latest
```

Suggested requirements.txt
```text
c2s-scale
# add any other pinned deps here, e.g.
# pyyaml==6.0
```

Suggested project files to add (next steps)
- example.py — small reproducible script demonstrating a typical experiment
- scripts/setup.sh and scripts/setup.ps1 — one-shot setup scripts that create venv and install pinned deps
- Dockerfile — as above
- .github/workflows/ci.yml — test matrix (python versions) that installs pinned deps and runs example.py

Minimal CI snippet (GitHub Actions)
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python: [3.10, 3.11]
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python }}
      - name: Install deps
        run: |
          python -m venv .venv
          source .venv/bin/activate
          pip install -U pip
          pip install -r requirements.txt
      - name: Run example
        run: |
          source .venv/bin/activate
          python example.py
```

Notes and tips
- Pin versions in requirements.txt for reproducibility.
- If c2s-scale is not on PyPI, include a submodule or install from git URL:
```bash
pip install git+https://github.com/<owner>/c2s-scale.git@<commit-or-tag>
```
- Prefer Docker for collaborators who don't want to configure environments.
- Add small example.py (<=30 lines) that demonstrates the minimal API and can be run by CI.

Next action (completed / next steps)
- Added example.py, requirements.txt, Dockerfile, scripts/setup.sh, scripts/setup.ps1, run_experiment.py, experiments/, experiments/eval_embeddings.py, and a CI workflow.
- Quick test (Unix):
  ```bash
  bash scripts/setup.sh
  source .venv/bin/activate
  export HF_TOKEN="hf_xxx"   # set your Hugging Face token
  python run_experiment.py --mode hf --model vandijklab/C2S-Scale-Gemma-2-27B --prompt-file experiments/example_prompt.txt
  ```
- To run via Ollama (if you host/import the model locally): install Ollama, import or convert the model to a format Ollama accepts, then:
  ```bash
  ollama run <model-name> --prompt "$(cat experiments/example_prompt.txt)"
  ```
- If you want, I can add an Ollama import/conversion helper and a small eval runner that saves outputs to experiments/outputs for embedding-based analysis.
