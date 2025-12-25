#!/usr/bin/env bash
# Lightweight helper to run the dashboard in this repo
set -euo pipefail

# Create venv if missing
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  echo "Created venv at ./.venv"
fi

# Activate venv for this script
source .venv/bin/activate

# Install requirements (safe no-op if already satisfied)
pip install -r requirements.txt

# Default port
PORT=${1:-5050}

echo "Starting dashboard on http://localhost:${PORT}"
python flask_app.py --port=${PORT}
