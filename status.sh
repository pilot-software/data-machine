#!/bin/bash
# Check HMS Terminology Service status

echo "🔍 Checking service status..."

if pgrep -f "uvicorn app.main:app" > /dev/null; then
    echo "✅ Service is RUNNING"
    echo ""
    echo "📊 Process info:"
    ps aux | grep "uvicorn app.main:app" | grep -v grep
    echo ""
    echo "🌐 Access points:"
    echo "   API Docs: http://localhost:8001/docs"
    echo "   Root: http://localhost:8001/"
    echo ""
    echo "🧪 Test:"
    echo "   curl http://localhost:8001/"
else
    echo "❌ Service is NOT running"
    echo ""
    echo "▶️  Start with: ./start.sh"
fi
