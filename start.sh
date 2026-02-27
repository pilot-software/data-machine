#!/bin/bash
# Start HMS Terminology Service

echo "Starting HMS Terminology Service..."

# Kill any existing instance
pkill -f "uvicorn app.main:app" 2>/dev/null || true
sleep 1

# Create logs directory
mkdir -p logs

# Load environment from .env so shell-exported values don't break startup
if [ -f ".env" ]; then
    set -a
    # shellcheck disable=SC1091
    . ./.env
    set +a
fi

# Normalize DEBUG to a valid boolean value if it was set to profile-like strings
case "${DEBUG:-}" in
    true|false|True|False|1|0|yes|no|on|off|"")
        ;;
    release|prod|production)
        export DEBUG=false
        ;;
    *)
        unset DEBUG
        ;;
esac

# Pick project Python so uvicorn is available without manual activation
if [ -x "venv/bin/python" ]; then
    PYTHON_BIN="venv/bin/python"
elif [ -x ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
else
    PYTHON_BIN="python3"
fi

# Start server in background
nohup "$PYTHON_BIN" -m uvicorn app.main:app --host 0.0.0.0 --port 8001 > logs/server.log 2>&1 &

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
