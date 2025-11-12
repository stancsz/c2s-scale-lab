import json
import os
from transformers import pipeline

os.makedirs("experiments/outputs", exist_ok=True)

with open("experiments/example_prompt.txt", "r", encoding="utf-8") as f:
    prompt = f.read()

gen = pipeline("text-generation", model="distilgpt2")
out = gen(prompt, max_new_tokens=512, do_sample=False, num_return_sequences=1)
text = out[0].get("generated_text", str(out))

with open("experiments/outputs/llm_research_summary.json", "w", encoding="utf-8") as f:
    json.dump({"prompt": prompt, "output": text}, f, indent=2, ensure_ascii=False)

print("Saved experiments/outputs/llm_research_summary.json")
