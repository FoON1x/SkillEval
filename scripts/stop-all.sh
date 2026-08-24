#!/usr/bin/env bash
#
# One-click stop both SkillEval services started by start-all.sh.
#
# Reads PIDs from .run/pids.json and kills the tracked processes AND their
# child trees (covers uvicorn --reload reloader children). Falls back to
# killing any process listening on the configured ports. Removes the PID
# file when done.
#
# Usage:
#   ./scripts/stop-all.sh
#
# Env overrides:
#   BACKEND_PORT=8000 FRONTEND_PORT=5173 ./scripts/stop-all.sh

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$REPO_ROOT/.run/pids.json"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

# Kill a process and all its descendants (Linux pkill -P recursion or pgrep -P).
kill_tree() {
  local root="$1"
  [[ -z "$root" ]] && return 0
  local children
  children=$(pgrep -P "$root" 2>/dev/null || true)
  for child in $children; do kill_tree "$child"; done
  if kill -0 "$root" 2>/dev/null; then
    kill -TERM "$root" 2>/dev/null || true
    sleep 0.2
    kill -KILL "$root" 2>/dev/null || true
  fi
}

kill_port() {
  local port="$1" pids=""
  if command -v ss >/dev/null 2>&1; then
    pids=$(ss -ltnp "sport = :$port" 2>/dev/null | grep -oE 'pid=[0-9]+' | cut -d= -f2 | sort -u)
  elif command -v lsof >/dev/null 2>&1; then
    pids=$(lsof -iTCP:"$port" -sTCP:LISTEN -t -P -n 2>/dev/null | sort -u)
  fi
  if [[ -z "$pids" ]]; then
    echo "No process listening on port $port."
    return 0
  fi
  for p in $pids; do
    kill_tree "$p"
    echo "Killed process tree on port $port (root PID $p)."
  done
}

stopped=0
if [[ -f "$PID_FILE" ]]; then
  # Parse PIDs with grep (avoid jq dependency).
  backend=$(grep -oE '"backend"[[:space:]]*:[[:space:]]*[0-9]+' "$PID_FILE" | grep -oE '[0-9]+$' || true)
  frontend=$(grep -oE '"frontend"[[:space:]]*:[[:space:]]*[0-9]+' "$PID_FILE" | grep -oE '[0-9]+$' || true)
  for pair in "backend:$backend" "frontend:$frontend"; do
    key="${pair%%:*}"; id="${pair##*:}"
    if [[ -n "$id" ]] && kill -0 "$id" 2>/dev/null; then
      kill_tree "$id"
      echo "Stopped $key (PID $id) and its children."
      stopped=$((stopped + 1))
    fi
  done
  rm -f "$PID_FILE"
else
  echo 'No PID file found (.run/pids.json); using port-based fallback.'
fi

# Port fallback: covers orphaned children and runs started outside start-all.sh.
kill_port "$BACKEND_PORT"
kill_port "$FRONTEND_PORT"

if [[ $stopped -eq 0 && ! -f "$PID_FILE" ]]; then
  echo 'No tracked processes were running.'
fi
echo 'Done.'
