#!/bin/bash
# Docker entrypoint script for Audio QA Application

set -e

echo "Starting Audio QA Application..."

# Wait for Redis to be ready
echo "Waiting for Redis..."
while ! redis-cli -h redis ping > /dev/null 2>&1; do
    echo "Redis is unavailable - sleeping"
    sleep 2
done
echo "Redis is ready!"

# Execute the provided command
exec "$@"
