#!/bin/bash

echo "Starting HMS Terminology Service..."

# Setup if first run
if [ "$1" = "setup" ]; then
    echo "Running setup..."
    python3 setup.py
    exit 0
fi

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Starting Redis..."
    redis-server --daemonize yes
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Start the FastAPI service
echo "Starting FastAPI service on http://localhost:8001"
uvicorn app.main:app --reload --port 8001 --host 0.0.0.0