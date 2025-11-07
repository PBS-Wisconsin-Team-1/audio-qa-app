
#!/bin/bash
# Bash script to stop all processes listed in scripts/tmp/auqa-pids.txt, recursively killing children

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$SCRIPT_DIR/tmp/auqa-pids.txt"

killtree() {
  local _pid=$1
  local _sig=${2:-TERM}
  for _child in $(pgrep -P $_pid); do
    killtree $_child $_sig
  done
  if kill -0 $_pid 2>/dev/null; then
    echo "Killing PID $_pid"
    kill -$_sig $_pid 2>/dev/null
  fi
}

if [[ -f "$PID_FILE" ]]; then
  while read -r pid; do
    if [[ "$pid" =~ ^[0-9]+$ ]]; then
      killtree $pid
    fi
  done < "$PID_FILE"
  rm -f "$PID_FILE"
else
  echo "No PID file found at $PID_FILE. Nothing to stop."
fi
