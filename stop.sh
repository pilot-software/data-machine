#!/bin/bash
# Stop HMS Terminology Service

echo "🛑 Stopping HMS Terminology Service..."

pkill -f "uvicorn app.main:app"

if [ $? -eq 0 ]; then
    echo "✅ Service stopped"
else
    echo "⚠️  No service running"
fi
