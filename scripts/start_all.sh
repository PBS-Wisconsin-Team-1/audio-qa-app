#!/bin/bash
# Bash script to start Redis server, RQ dashboard, and queue_cli.py
# Assumes redis-server is in PATH

cd "$(dirname "$0")/../src/job_queue"

# Start redis-server in a new terminal window
gnome-terminal -- bash -c "redis-server; exec bash" 2>/dev/null || x-terminal-emulator -e "redis-server" &

# Start rq-dashboard in a new terminal window
gnome-terminal -- bash -c "rq-dashboard; exec bash" 2>/dev/null || x-terminal-emulator -e "rq-dashboard" &

# Run the CLI in the current terminal
python queue_cli.py
