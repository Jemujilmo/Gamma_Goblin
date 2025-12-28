#!/usr/bin/env bash
# Lightweight helper to run the dashboard in this repo
set -euo pipefail

# Create venv if missing
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  echo "Created venv at ./.venv"
fi

# Use the venv python directly instead of sourcing the activate script.
# Sourcing can interact with the user's tty and cause background jobs to be suspended.
VENV_PY="./.venv/bin/python"

# Install requirements using the venv python (safe no-op if already satisfied)
"$VENV_PY" -m pip install -r requirements.txt

# Default port
PORT=${1:-5050}

echo "Starting dashboard on http://localhost:${PORT}"
# Exec the venv python so the script PID is replaced by the Python process.
exec "$VENV_PY" flask_app.py --port=${PORT}
