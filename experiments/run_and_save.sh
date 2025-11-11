#!/usr/bin/env bash
# experiments/run_and_save.sh
# Run run_experiment.py (or ollama) and save stdout to a timestamped file in experiments/outputs
# Usage:
#   bash experiments/run_and_save.sh [model] [mode] [prompt-file] [max-tokens]
# Example:
#   bash experiments/run_and_save.sh vandijklab/C2S-Scale-Gemma-2-27B hf experiments/example_prompt.txt 512

set -euo pipefail

OUTDIR="experiments/outputs"
mkdir -p "$OUTDIR"

MODEL="${1:-vandijklab/C2S-Scale-Gemma-2-27B}"
MODE="${2:-hf}"   # hf | ollama | local
PROMPT_FILE="${3:-experiments/example_prompt.txt}"
MAX_TOK="${4:-512}"

TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
OUTFILE="$OUTDIR/run-${MODE}-${TIMESTAMP}.txt"

echo "Running model=$MODEL mode=$MODE prompt=$PROMPT_FILE -> $OUTFILE"

if [ "$MODE" = "ollama" ]; then
  if ! command -v ollama >/dev/null 2>&1; then
    echo "ollama not found on PATH. Install from https://ollama.com" > "$OUTFILE"
    echo "Failed: ollama missing"
    exit 2
  fi
  # Use ollama run and capture stdout/stderr
  ollama run "$MODEL" --prompt "$(cat "$PROMPT_FILE")" > "$OUTFILE" 2>&1 || true
else
  # Default: use Python harness
  if ! command -v python >/dev/null 2>&1; then
    echo "python not found on PATH" > "$OUTFILE"
    echo "Failed: python missing"
    exit 3
  fi
  python run_experiment.py --mode "$MODE" --model "$MODEL" --prompt-file "$PROMPT_FILE" --max-tokens "$MAX_TOK" > "$OUTFILE" 2>&1 || true
fi

echo "Wrote output to $OUTFILE"
