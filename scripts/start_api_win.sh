#!/bin/bash
# Bash script to start the API server in a new terminal window (Windows WSL/Ubuntu or Linux)
# Usage: bash start_api_win.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
JOB_QUEUE_DIR="$SCRIPT_DIR/../job_queue/src"

gnome-terminal --title="AUQA-API" -- bash -c "cd $JOB_QUEUE_DIR && python api_server.py; exec bash" 2>/dev/null &