#!/bin/bash
# Start the Flask API server for the frontend

cd "$(dirname "$0")/../src/job_queue"
python api_server.py

