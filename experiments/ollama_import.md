# Ollama import / local hosting notes (high-level)

Goal
- If you want to run the Vandijklab C2S-Scale Gemma model locally with Ollama, these are safe, reproducible steps and links. This document does NOT bundle model weights; follow licensing in the model repo before downloading.

Two safe options
1) Use Hugging Face Inference API (fast, requires HF token)
   - Easiest: no local heavy compute, no conversion.
   - Use: `python run_experiment.py --mode hf --model vandijklab/C2S-Scale-Gemma-2-27B --prompt-file experiments/example_prompt.txt`
2) Host locally with Ollama (requires model weights + conversion to a format Ollama accepts)
   - Use this only if you have rights to download the weights (check the HF repo license).

High-level Ollama import flow
1. Inspect the HF repo and license
   - URL (example): https://huggingface.co/vandijklab/C2S-Scale-Gemma-2-27B
   - Confirm licenses and usage restrictions before downloading weights.

2. Download the model repository (weights + config)
   - Recommended: use `huggingface-cli` or `git lfs` as directed by the model repo.
   - Example:
     ```bash
     pip install huggingface_hub
     python -c "from huggingface_hub import snapshot_download; snapshot_download('vandijklab/C2S-Scale-Gemma-2-27B', cache_dir='./hf-models/gemma')"
     ```

3. Convert weights to a format Ollama accepts
   - Ollama commonly supports GGUF/ggml style model files produced by the llama.cpp toolchain or other supported formats.
   - Popular conversion utilities:
     - llama.cpp's conversion scripts (see llama.cpp repo for convert scripts that produce gguf/ggml)
     - `transformers` -> `gguf` converters maintained in community repos
   - Example (conceptual):
     ```bash
     # after downloading HF files into ./hf-models/gemma
     # use a conversion script (community tool) to produce gemma.gguf
     python convert-hf-to-gguf.py --repo-dir ./hf-models/gemma --out ./gguf/gemma.gguf
     ```
   - Converters and exact commands vary by model architecture; consult the converter README.

4. Import into Ollama (conceptual)
   - If Ollama supports a direct import:
     ```bash
     ollama import ./gguf/gemma.gguf --name gemma
     ```
   - Or follow Ollama docs for locally-hosted custom models and place the gguf in Ollama's model folder.

5. Run with Ollama
   - Interactive:
     ```bash
     ollama chat gemma
     ```
   - One-off:
     ```bash
     ollama run gemma --prompt "$(cat experiments/example_prompt.txt)"
     ```

Practical notes and troubleshooting
- Conversions may fail if the HF repo stores sharded weights or uses an unsupported architecture. Check converter tool issues for model-specific guidance.
- Converting large models requires substantial disk space, memory, and time.
- If conversion is difficult, use HF Inference API to avoid local hosting complexity.
- Always verify the model output for hallucinations and unsafe content before use in any downstream workflow.

Links and tools
- Hugging Face hub docs: https://huggingface.co/docs/hub
- Ollama docs (import/custom model guidance): https://ollama.com/docs
- llama.cpp repo (conversion utilities): https://github.com/ggerganov/llama.cpp

If you want, I can:
- Add a small helper script that downloads the HF repo snapshot to ./hf-models/gemma (download-only, no conversion).
- Add example conversion command templates (non-executable placeholders) referencing popular community converters.
