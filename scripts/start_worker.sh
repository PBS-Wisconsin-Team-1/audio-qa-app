#!/bin/bash
# Start an RQ worker for processing audio detection jobs

cd "$(dirname "$0")/.."
cd src/job_queue
PYTHONPATH=../../src rq worker --worker-class rq.SimpleWorker

