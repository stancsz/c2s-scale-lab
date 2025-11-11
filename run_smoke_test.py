#!/usr/bin/env python3
import sys
import traceback

def main():
    try:
        from transformers import pipeline
        gen = pipeline("text-generation", model="distilgpt2")
        out = gen("Testing run_experiment local smoke test", max_new_tokens=32, do_sample=False, num_return_sequences=1)
        if isinstance(out, list) and out and isinstance(out[0], dict):
            text = out[0].get("generated_text", str(out))
        else:
            text = str(out)
        print(text)
    except Exception as e:
        print("ERROR:", e, file=sys.stderr)
        traceback.print_exc()
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
