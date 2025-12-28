#!/usr/bin/env bash
set -euo pipefail

# start_dashboard_detach.sh
# Reliable helper to start the dashboard detached and wait for the API to respond.

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

PORT=${1:-5050}
API_URL="http://127.0.0.1:${PORT}/api/analysis"
VENV_PY="./.venv/bin/python"
LOGFILE="dashboard.log"
PIDFILE="dashboard.pid"

echo "[dashboard helper] ensuring port ${PORT} is free..."
if command -v lsof >/dev/null 2>&1; then
  lsof -tiTCP:${PORT} -sTCP:LISTEN | xargs -r -n1 kill || true
fi

echo "[dashboard helper] installing requirements (if needed)"
"$VENV_PY" -m pip install -r requirements.txt >/dev/null 2>&1 || true

echo "[dashboard helper] starting dashboard on http://localhost:${PORT}"
# start detached, detach stdin and stdout/stderr to logfile
nohup "$VENV_PY" flask_app.py --port=${PORT} > "$LOGFILE" 2>&1 < /dev/null &
echo $! > "$PIDFILE"

echo "[dashboard helper] waiting for API to respond (timeout 20s)"
SECS=0
MAX=20
until curl -sS "$API_URL" >/dev/null 2>&1; do
  sleep 1
  ((SECS++))
  if [ $SECS -ge $MAX ]; then
    echo "[dashboard helper] timeout waiting for API (check $LOGFILE)"
    echo "--- last 80 lines of $LOGFILE ---"
    tail -n 80 "$LOGFILE" || true
    exit 1
  fi
done

echo "[dashboard helper] API is responding after ${SECS}s"
echo "--- first 120 lines of $LOGFILE ---"
head -n 120 "$LOGFILE" || true

echo "You can follow logs with: tail -f $LOGFILE"
echo "To stop: kill \$(cat $PIDFILE) && rm $PIDFILE"
