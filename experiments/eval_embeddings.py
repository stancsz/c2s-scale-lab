#!/usr/bin/env python3
"""
eval_embeddings.py

Compute embedding-based similarity between model outputs to measure stability
and clustering of responses across prompt variants or runs.

Usage:
  python experiments/eval_embeddings.py --outputs-dir experiments/outputs --model all-MiniLM-L6-v2

Expectations:
 - outputs-dir contains plain .txt files; each file is treated as one model response.
 - The script writes results to outputs_dir/similarity_report.json and prints a short table.

Dependencies:
  pip install sentence-transformers numpy scipy

This script is defensive and will print actionable instructions if deps are missing.
"""
import argparse
import json
from pathlib import Path
import sys

def load_texts(outputs_dir):
    p = Path(outputs_dir)
    if not p.exists():
        print("Outputs directory not found:", outputs_dir, file=sys.stderr)
        return None
    files = sorted([f for f in p.iterdir() if f.is_file() and f.suffix.lower() == ".txt"])
    texts = []
    for f in files:
        try:
            texts.append({"path": str(f), "text": f.read_text(encoding="utf-8")})
        except Exception as e:
            print(f"Failed to read {f}: {e}", file=sys.stderr)
    return texts

def main():
    parser = argparse.ArgumentParser(description="Compute embedding similarity across model outputs")
    parser.add_argument("--outputs-dir", default="experiments/outputs", help="Directory containing .txt outputs")
    parser.add_argument("--model", default="all-MiniLM-L6-v2", help="Sentence-Transformers model for embeddings")
    parser.add_argument("--out-json", default=None, help="Path to save JSON report (default: outputs-dir/similarity_report.json)")
    args = parser.parse_args()

    texts = load_texts(args.outputs_dir)
    if texts is None or len(texts) == 0:
        print("No .txt output files found in", args.outputs_dir, file=sys.stderr)
        print("Create experiment outputs by running run_experiment.py and saving responses to files named e.g. experiments/outputs/run1.txt", file=sys.stderr)
        return 2

    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        from scipy.spatial.distance import pdist, squareform
    except Exception as e:
        print("Missing dependencies for embedding eval.", file=sys.stderr)
        print("Install with: pip install sentence-transformers numpy scipy", file=sys.stderr)
        print("Detailed error:", e, file=sys.stderr)
        return 3

    model = SentenceTransformer(args.model)
    corpus = [t["text"] for t in texts]
    embeddings = model.encode(corpus, convert_to_numpy=True, show_progress_bar=True)

    # pairwise cosine similarity
    dists = squareform(pdist(embeddings, metric="cosine"))
    sims = 1.0 - dists

    # build report
    names = [Path(t["path"]).name for t in texts]
    report = {
        "model": args.model,
        "outputs_dir": args.outputs_dir,
        "files": names,
        "similarity_matrix": sims.tolist()
    }

    out_json = args.out_json or str(Path(args.outputs_dir) / "similarity_report.json")
    Path(out_json).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote similarity report to {out_json}")

    # print brief summary: average pairwise similarity and top/bottom pairs
    import itertools
    n = len(names)
    pairs = []
    for i, j in itertools.combinations(range(n), 2):
        pairs.append(((names[i], names[j]), float(sims[i][j])))
    pairs_sorted = sorted(pairs, key=lambda x: x[1], reverse=True)

    avg_sim = float(sum([p[1] for p in pairs]) / max(1, len(pairs)))
    print(f"Files evaluated: {n}")
    print(f"Average pairwise cosine similarity: {avg_sim:.4f}")
    print("Top 3 most similar pairs:")
    for (a,b),s in pairs_sorted[:3]:
        print(f"  {a} <-> {b}: {s:.4f}")
    print("Top 3 least similar pairs:")
    for (a,b),s in pairs_sorted[-3:]:
        print(f"  {a} <-> {b}: {s:.4f}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
