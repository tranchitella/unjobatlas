#!/bin/bash
# Script to run Celery worker for UNJobAtlas

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run Celery worker with concurrency of 1 to process jobs sequentially
celery -A config worker --loglevel=info --concurrency=1
