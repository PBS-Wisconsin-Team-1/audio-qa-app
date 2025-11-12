#!/bin/bash
# Start the Flask API server for the frontend

cd "$(dirname "$0")/.."
python src/api_server.py

