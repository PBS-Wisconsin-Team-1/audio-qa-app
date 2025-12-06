
#!/bin/bash
# Bash script to stop all processes listed in scripts/tmp/auqa-pids.txt, recursively killing children
# Works on both Linux and macOS

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$SCRIPT_DIR/tmp/auqa-pids.txt"

killtree() {
  local _pid=$1
  local _sig=${2:-TERM}
  # Use pgrep -P on both Linux and macOS (works the same way)
  for _child in $(pgrep -P $_pid 2>/dev/null); do
    killtree $_child $_sig
  done
  if kill -0 $_pid 2>/dev/null; then
    echo "Killing PID $_pid"
    kill -$_sig $_pid 2>/dev/null
  fi
}

# Also kill processes by name pattern (useful if PID file is missing or incomplete)
kill_by_pattern() {
  local pattern=$1
  local name=$2
  local pids=$(pgrep -f "$pattern" 2>/dev/null | grep -v $$)
  if [[ -n "$pids" ]]; then
    echo "Stopping $name processes..."
    for pid in $pids; do
      killtree $pid
    done
  fi
}

if [[ -f "$PID_FILE" ]]; then
  echo "Stopping processes from PID file..."
  while read -r pid; do
    if [[ "$pid" =~ ^[0-9]+$ ]]; then
      killtree $pid
    fi
  done < "$PID_FILE"
  rm -f "$PID_FILE"
else
  echo "No PID file found. Stopping processes by pattern..."
fi

# Also stop processes by name pattern (backup method, especially useful on macOS)
kill_by_pattern "python.*api_server.py" "API Server"
kill_by_pattern "rq worker" "RQ Workers"
kill_by_pattern "rq-dashboard" "RQ Dashboard"
kill_by_pattern "python.*queue_cli.py" "Queue CLI"

# Note: We don't kill redis-server as it might be used by other applications
# If you want to kill Redis too, uncomment the next line:
# kill_by_pattern "redis-server" "Redis Server"

echo "Done!"
