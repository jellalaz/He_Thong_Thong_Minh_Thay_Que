#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
# Uses the Python selected by the user (including an activated Miniforge env).
# pip is always invoked through the project venv, never through conda base.
python3 -m venv .venv
.venv/bin/python -m pip install --cache-dir .runtime/pip-cache -r requirements-macos-lock.txt
.venv/bin/python scripts/setup_macos.py
echo 'Setup complete. Start with: bash run-macos.sh'
