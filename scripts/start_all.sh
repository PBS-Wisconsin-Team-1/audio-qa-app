#!/bin/bash
# Bash script to start Redis server, RQ dashboard, and multiple rq workers, then run queue_cli.py

# Usage: bash start_all.sh [num_workers] [--dashboard]

WORKERS=${1:-1}
DASHBOARD=0
if [[ "$2" == "--dashboard" ]]; then
  DASHBOARD=1
fi
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
JOB_QUEUE_DIR="$SCRIPT_DIR/../src/job_queue"
PID_DIR="$SCRIPT_DIR/tmp"
PID_FILE="$PID_DIR/auqa-pids.txt"
mkdir -p "$PID_DIR"
echo -n > "$PID_FILE"

# Start redis-server in a new terminal window and record its PID
gnome-terminal -- bash -c "redis-server; exec bash" 2>/dev/null &
REDIS_PID=$!
echo $REDIS_PID >> "$PID_FILE"


# Optionally start rq-dashboard
if [[ $DASHBOARD -eq 1 ]]; then
  gnome-terminal --title="AUQA-DASHBOARD" -- bash -c "rq-dashboard; exec bash" 2>/dev/null &
  DASH_PID=$!
  echo $DASH_PID >> "$PID_FILE"
fi

for i in $(seq 1 $WORKERS); do
  gnome-terminal --title="AUQA-WORKER-$i" -- bash -c "cd $JOB_QUEUE_DIR && rq worker; exec bash" 2>/dev/null &
  WORKER_PID=$!
  echo $WORKER_PID >> "$PID_FILE"
done

# Start API server in a new terminal window with a unique title and record its PID
API_DIR="$SCRIPT_DIR/../src"
gnome-terminal --title="AUQA-API" -- bash -c "cd $API_DIR && python api_server.py; exec bash" 2>/dev/null &
API_PID=$!
echo $API_PID >> "$PID_FILE"

# Start the queue consumer in a new terminal window with a unique title and record its PID
sleep 3
gnome-terminal --title="AUQA-QUEUER" -- bash -c "cd $JOB_QUEUE_DIR && python queue_cli.py; exec bash" 2>/dev/null &
QUEUER_PID=$!
echo $QUEUER_PID >> "$PID_FILE"