#!/bin/bash
# Bash script to start Redis server, RQ dashboard, and multiple rq workers, then run queue_cli.py
# Works on both Linux and macOS

# Usage: bash start_all.sh [num_workers] [--dashboard]

WORKERS=${1:-1}
DASHBOARD=0
if [[ "$2" == "--dashboard" ]]; then
  DASHBOARD=1
fi
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
JOB_QUEUE_DIR="$SCRIPT_DIR/../src/job_queue"
API_DIR="$SCRIPT_DIR/../src/job_queue"
PID_DIR="$SCRIPT_DIR/tmp"
PID_FILE="$PID_DIR/auqa-pids.txt"
FRONTEND_DIR="$SCRIPT_DIR/../frontend"
mkdir -p "$PID_DIR"
echo -n > "$PID_FILE"

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

# Function to open a new terminal window
open_terminal() {
    local title=$1
    local command=$2
    
    if [[ "$MACHINE" == "Mac" ]]; then
        # macOS: Use osascript to open Terminal.app
        osascript -e "tell application \"Terminal\" to do script \"cd '$SCRIPT_DIR/..' && $command\""
    elif [[ "$MACHINE" == "Linux" ]]; then
        # Linux: Use gnome-terminal
        gnome-terminal --title="$title" -- bash -c "$command; exec bash" 2>/dev/null &
    else
        echo "Unsupported OS: $MACHINE. Please run commands manually."
        return 1
    fi
}

# Check if Redis is already running
if redis-cli ping > /dev/null 2>&1; then
    echo "Redis server is already running."
else
    # Start redis-server in a new terminal window
    echo "Starting Redis server..."
    if [[ "$MACHINE" == "Mac" ]]; then
        osascript -e "tell application \"Terminal\" to activate" -e "tell application \"Terminal\" to do script \"redis-server\"" > /dev/null 2>&1 &
    elif [[ "$MACHINE" == "Linux" ]]; then
        gnome-terminal --title="AUQA-REDIS" -- bash -c "redis-server; exec bash" 2>/dev/null &
    fi
    sleep 2
fi

# Optionally start rq-dashboard
if [[ $DASHBOARD -eq 1 ]]; then
    echo "Starting RQ Dashboard..."
    if [[ "$MACHINE" == "Mac" ]]; then
        osascript -e "tell application \"Terminal\" to activate" -e "tell application \"Terminal\" to do script \"rq-dashboard\"" > /dev/null 2>&1 &
    elif [[ "$MACHINE" == "Linux" ]]; then
        gnome-terminal --title="AUQA-DASHBOARD" -- bash -c "rq-dashboard; exec bash" 2>/dev/null &
    fi
    sleep 1
fi

# Start RQ Workers
for i in $(seq 1 $WORKERS); do
    echo "Starting RQ Worker $i..."
    if [[ "$MACHINE" == "Mac" ]]; then
        osascript -e "tell application \"Terminal\" to activate" -e "tell application \"Terminal\" to do script \"cd '$JOB_QUEUE_DIR' && PYTHONPATH=../../src rq worker --worker-class rq.SimpleWorker\"" > /dev/null 2>&1 &
    elif [[ "$MACHINE" == "Linux" ]]; then
        gnome-terminal --title="AUQA-WORKER-$i" -- bash -c "cd $JOB_QUEUE_DIR && PYTHONPATH=../../src rq worker --worker-class rq.SimpleWorker; exec bash" 2>/dev/null &
    fi
    sleep 1
done

# Start API server in a new terminal window
echo "Starting API server..."
if [[ "$MACHINE" == "Mac" ]]; then
    osascript -e "tell application \"Terminal\" to activate" -e "tell application \"Terminal\" to do script \"cd '$SCRIPT_DIR/..' && auqa-api\"" > /dev/null 2>&1 &
elif [[ "$MACHINE" == "Linux" ]]; then
    gnome-terminal --title="AUQA-API" -- bash -c "cd $SCRIPT_DIR/.. && auqa-api; exec bash" 2>/dev/null &
fi
sleep 2

# Start the queue CLI in a new terminal window
echo "Starting Queue CLI..."
if [[ "$MACHINE" == "Mac" ]]; then
    osascript -e "tell application \"Terminal\" to activate" -e "tell application \"Terminal\" to do script \"cd '$FRONTEND_DIR/..' && npm start\"" > /dev/null 2>&1 &
elif [[ "$MACHINE" == "Linux" ]]; then
    gnome-terminal --title="AUQA-QUEUER" -- bash -c "cd $FRONTEND_DIR && npm start; exec bash" 2>/dev/null &
fi
sleep 2
echo ""
echo "⚠️  Check your Terminal app - new windows should have opened!"
echo "   Look for windows/tabs with the Queue CLI menu."

echo ""
echo "All services started!"
if [[ $DASHBOARD -eq 1 ]]; then
    echo "RQ Dashboard: http://localhost:9181"
fi
echo "API Server: http://localhost:5001"
echo "Frontend: http://localhost:3000 (if running)"
echo ""
echo "To stop all services, run: bash scripts/stop_all.sh"