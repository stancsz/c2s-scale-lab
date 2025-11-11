#!/usr/bin/env python3
"""
run_experiment.py -- simple harness to run prompts against a C2S-Scale model.

Supports three modes:
 - hf     : Hugging Face Inference API (requires HF_TOKEN env var)
 - ollama : call a locally-running Ollama model (requires `ollama` on PATH)
 - local  : try to load model locally via transformers (requires GPU, large RAM, bitsandbytes, accelerate, torch)

Usage examples:
  python run_experiment.py --mode hf --model vandijklab/C2S-Scale-Gemma-2-27B --prompt-file experiments/example_prompt.txt
  python run_experiment.py --mode ollama --model gemma --prompt-file experiments/example_prompt.txt
  python run_experiment.py --mode local --model ./local-model-dir --prompt-file experiments/example_prompt.txt

The script is defensive and prints actionable errors when requirements are missing.
"""
import argparse
import os
import sys
import json
import subprocess
from pathlib import Path

def read_prompt(path):
    return Path(path).read_text(encoding="utf-8")

def run_hf_inference(model, prompt, max_tokens=512):
    import requests
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_TOKEN")
    if not token:
        print("Hugging Face token not found. Set HF_TOKEN environment variable.", file=sys.stderr)
        return 1
    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": max_tokens}}
    print(f"Calling Hugging Face Inference API: {url} (this may consume your HF quotas)")
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    if resp.status_code != 200:
        print("HF API error:", resp.status_code, resp.text, file=sys.stderr)
        return 2
    try:
        data = resp.json()
        # HF sometimes returns list of dicts, or plain text; handle common cases
        if isinstance(data, dict) and "generated_text" in data:
            output = data["generated_text"]
        elif isinstance(data, list) and len(data) and isinstance(data[0], dict) and "generated_text" in data[0]:
            output = data[0]["generated_text"]
        else:
            output = json.dumps(data, indent=2)
        print(output)
    except Exception as e:
        print("Failed to parse HF response:", e, file=sys.stderr)
        print(resp.text)
        return 3
    return 0

def run_ollama(model, prompt, max_tokens=512):
    # Uses `ollama run <model> --prompt "<prompt>"`
    cmd = ["ollama", "run", model, "--prompt", prompt]
    print("Running Ollama command:", " ".join(cmd))
    try:
        cp = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=300)
    except FileNotFoundError:
        print("ollama not found on PATH. Install from https://ollama.com", file=sys.stderr)
        return 1
    except subprocess.TimeoutExpired:
        print("Ollama run timed out.", file=sys.stderr)
        return 2
    if cp.returncode != 0:
        print("Ollama returned non-zero code:", cp.returncode, file=sys.stderr)
        print(cp.stderr, file=sys.stderr)
        return cp.returncode
    print(cp.stdout)
    return 0

def run_local_transformers(model, prompt, max_tokens=512):
    print("Attempting to run model locally via transformers. This requires torch, transformers, accelerate and possibly bitsandbytes.")
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    except Exception as e:
        print("Missing dependencies for local run. Install with:", file=sys.stderr)
        print("  pip install torch transformers accelerate bitsandbytes", file=sys.stderr)
        print("Detailed error:", e, file=sys.stderr)
        return 1

    # Best-effort attempt to load model with device_map='auto'
    try:
        print(f"Loading tokenizer for {model} ...")
        tokenizer = AutoTokenizer.from_pretrained(model, use_fast=True)
        print("Loading model (this may take a long time and require lots of GPU RAM)...")
        model_obj = AutoModelForCausalLM.from_pretrained(model,
                                                         device_map="auto",
                                                         torch_dtype=torch.float16,
                                                         low_cpu_mem_usage=True)
        gen = pipeline("text-generation", model=model_obj, tokenizer=tokenizer, device=0 if torch.cuda.is_available() else -1)
        out = gen(prompt, max_new_tokens=max_tokens, do_sample=False, num_return_sequences=1)
        text = out[0]["generated_text"] if isinstance(out, list) and out and "generated_text" in out[0] else str(out)
        print(text)
    except Exception as e:
        print("Failed to run local model:", e, file=sys.stderr)
        return 2
    return 0

def main():
    p = argparse.ArgumentParser(description="Run a prompt against a C2S-Scale model via hf/ollama/local")
    p.add_argument("--mode", choices=["hf","ollama","local"], default="hf", help="Execution mode")
    p.add_argument("--model", default="vandijklab/C2S-Scale-Gemma-2-27B", help="Model id or name")
    p.add_argument("--prompt-file", default="experiments/example_prompt.txt", help="Prompt file path")
    p.add_argument("--max-tokens", type=int, default=512)
    args = p.parse_args()

    if not Path(args.prompt_file).exists():
        print("Prompt file not found:", args.prompt_file, file=sys.stderr)
        return 10
    prompt = read_prompt(args.prompt_file)

    if args.mode == "hf":
        return run_hf_inference(args.model, prompt, args.max_tokens)
    elif args.mode == "ollama":
        return run_ollama(args.model, prompt, args.max_tokens)
    elif args.mode == "local":
        return run_local_transformers(args.model, prompt, args.max_tokens)
    else:
        print("Unknown mode:", args.mode, file=sys.stderr)
        return 20

if __name__ == "__main__":
    sys.exit(main())
