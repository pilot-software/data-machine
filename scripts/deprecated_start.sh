#!/bin/bash

echo "🚀 Starting HMS Terminology Service..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
fi

# Check if database is setup
echo "📊 Checking database connection..."
python -c "from app.db.database import engine; engine.connect()" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Database not configured. Please run: python setup_full_db.py"
    exit 1
fi

# Start the service
echo "✅ Starting API server on http://localhost:8001"
echo "📚 Swagger UI: http://localhost:8001/docs"
echo "📖 ReDoc: http://localhost:8001/redoc"
echo ""

python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
