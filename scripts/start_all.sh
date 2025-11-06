#!/bin/bash
# Bash script to start Redis server, RQ dashboard, and queue_cli.py
# Assumes redis-server is in PATH

cd "$(dirname "$0")/../src/job_queue"
redis-server &
rq-dashboard &
python queue_cli.py
