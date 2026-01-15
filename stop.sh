#!/bin/bash
# Stop HMS Terminology Service

echo "Stopping HMS Terminology Service..."

pkill -f "uvicorn app.main:app"

if [ $? -eq 0 ]; then
    echo "✅ Server stopped"
else
    echo "⚠️  No server running"
fi
