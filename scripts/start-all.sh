#!/usr/bin/env bash
#
# One-click start both SkillEval services (FastAPI backend + Vite frontend) in the background.
#
# Prerequisites:
#   - apps/api/.venv  (run `uv sync` in apps/api)
#   - apps/web/node_modules  (run `npm install` in apps/web)
#
# Usage:
#   ./scripts/start-all.sh              # plain (no reload)
#   ./scripts/start-all.sh --reload     # uvicorn --reload
#
# PIDs are saved to .run/pids.json for stop-all.sh.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$REPO_ROOT/apps/api"
WEB_DIR="$REPO_ROOT/apps/web"
RUN_DIR="$REPO_ROOT/.run"
PID_FILE="$RUN_DIR/pids.json"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
RELOAD=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --reload) RELOAD="--reload"; shift ;;
    *) echo "unknown arg: $1" >&2; exit 1 ;;
  esac
done

port_in_use() {
  if command -v ss >/dev/null 2>&1; then
    ss -ltn "sport = :$1" 2>/dev/null | grep -q ":$1"
  elif command -v lsof >/dev/null 2>&1; then
    lsof -iTCP:"$1" -sTCP:LISTEN -P -n 2>/dev/null | grep -q ":$1"
  else
    return 1
  fi
}

mkdir -p "$RUN_DIR"

if [[ ! -f "$API_DIR/.venv/bin/python" && ! -f "$API_DIR/.venv/Scripts/python.exe" ]]; then
  echo "Backend venv not found in $API_DIR/.venv. Run 'uv sync' in apps/api first." >&2
  exit 1
fi
if [[ ! -d "$WEB_DIR/node_modules" ]]; then
  echo "Frontend node_modules not found. Run 'npm install' in apps/web first." >&2
  exit 1
fi
if port_in_use "$BACKEND_PORT"; then echo "Port $BACKEND_PORT already in use." >&2; exit 1; fi
if port_in_use "$FRONTEND_PORT"; then echo "Port $FRONTEND_PORT already in use." >&2; exit 1; fi

# Pick the python for this platform.
if [[ -f "$API_DIR/.venv/Scripts/python.exe" ]]; then
  PY="$API_DIR/.venv/Scripts/python.exe"
else
  PY="$API_DIR/.venv/bin/python"
fi

# --- Start backend (background, nohup so it survives shell exit) ---
(
  cd "$API_DIR"
  exec "$PY" -m uvicorn skill_eval.main:app --port "$BACKEND_PORT" $RELOAD
) >/dev/null 2>&1 &
BACKEND_PID=$!
echo "Backend started (PID $BACKEND_PID) on port $BACKEND_PORT${RELOAD:+ [reload]}"

# --- Start frontend ---
(
  cd "$WEB_DIR"
  exec npm run dev
) >/dev/null 2>&1 &
FRONTEND_PID=$!
echo "Frontend started (PID $FRONTEND_PID) on port $FRONTEND_PORT"

cat >"$PID_FILE" <<EOF
{
  "backend": $BACKEND_PID,
  "frontend": $FRONTEND_PID,
  "backendPort": $BACKEND_PORT,
  "frontendPort": $FRONTEND_PORT
}
EOF

# --- Health check ---
wait_healthy() {
  local url="$1" name="$2" timeout="${3:-40}" deadline
  deadline=$(( $(date +%s) + timeout ))
  while [[ $(date +%s) -lt $deadline ]]; do
    if curl -sf -o /dev/null --max-time 2 "$url" 2>/dev/null; then
      echo "$name ready."
      return 0
    fi
    sleep 0.5
  done
  echo "$name did not become healthy within ${timeout}s." >&2
  return 1
}

wait_healthy "http://127.0.0.1:$BACKEND_PORT/health" 'Backend'
wait_healthy "http://localhost:$FRONTEND_PORT/" 'Frontend' 30 || true

echo
echo "Services running. Open http://localhost:$FRONTEND_PORT"
echo "Run scripts/stop-all.sh to stop."
