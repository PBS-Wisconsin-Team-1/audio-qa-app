#!/bin/bash
# Start the queue CLI for processing audio files

cd "$(dirname "$0")/.."
PYTHONPATH=src python src/job_queue/queue_cli.py

