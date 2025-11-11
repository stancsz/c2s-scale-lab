#!/usr/bin/env bash
# scripts/setup.sh - create virtualenv and install pinned requirements
# Usage:
#   bash scripts/setup.sh
# Notes:
#  - This script creates a .venv directory and installs requirements.txt.
#  - To activate the venv after running: source .venv/bin/activate

set -euo pipefail

VENV_DIR=".venv"

echo "Creating virtual environment at ${VENV_DIR}..."
python -m venv "${VENV_DIR}"

echo "Activating virtual environment..."
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

echo "Upgrading pip, setuptools, wheel..."
pip install --upgrade pip setuptools wheel

if [ -f "requirements.txt" ]; then
  echo "Installing requirements from requirements.txt..."
  pip install --no-cache-dir -r requirements.txt
else
  echo "No requirements.txt found — skipping pip install."
fi

echo "Setup complete. Activate with: source ${VENV_DIR}/bin/activate"
