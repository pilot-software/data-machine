#!/bin/bash
# Start HMS Terminology Service

echo "Starting HMS Terminology Service..."

# Kill any existing instance
pkill -f "uvicorn app.main:app" 2>/dev/null || true
sleep 1

# Create logs directory
mkdir -p logs

# Start server in background
nohup uvicorn app.main:app --host 0.0.0.0 --port 8001 > logs/server.log 2>&1 &

# Wait for server to start
sleep 3

# Check if running
if curl -s http://localhost:8001/api/v1/health > /dev/null 2>&1; then
    echo "✅ Server started successfully on http://localhost:8001"
    echo "📖 API Docs: http://localhost:8001/docs"
    echo "📝 Logs: tail -f logs/server.log"
else
    echo "❌ Server failed to start. Check logs/server.log"
    exit 1
fi
