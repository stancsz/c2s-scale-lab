# scripts/setup.ps1 - create virtualenv and install pinned requirements (PowerShell)
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
# Notes:
#  - This script creates a .venv directory and installs requirements.txt.
#  - To activate the venv after running: .\.venv\Scripts\Activate.ps1

Param(
  [string]$VenvDir = ".venv"
)

Write-Output "Creating virtual environment at $VenvDir..."
python -m venv $VenvDir

Write-Output "Activating virtual environment..."
# The user should run the activation command themselves in their shell after the script runs.
Write-Output "To activate: .\$VenvDir\Scripts\Activate.ps1"

Write-Output "Upgrading pip, setuptools, wheel..."
& "$VenvDir\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel

if (Test-Path -Path "requirements.txt") {
  Write-Output "Installing requirements from requirements.txt..."
  & "$VenvDir\Scripts\python.exe" -m pip install --no-cache-dir -r requirements.txt
} else {
  Write-Output "No requirements.txt found — skipping pip install."
}

Write-Output "Setup complete. Activate with: .\$VenvDir\Scripts\Activate.ps1"
