#!/bin/bash

echo "🚀 Starting HMS Terminology Service..."
echo ""

# Restart PostgreSQL to clear all connections
echo "🔧 Restarting PostgreSQL..."
brew services restart postgresql@14 > /dev/null 2>&1 || brew services restart postgresql > /dev/null 2>&1
sleep 3

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "📦 Starting Redis..."
    redis-server --daemonize yes
fi

# Drop and recreate database
echo "📊 Recreating database..."
psql -d postgres -c "DROP DATABASE IF EXISTS hms_terminology;" > /dev/null 2>&1
psql -d postgres -c "CREATE DATABASE hms_terminology;" > /dev/null 2>&1

echo "⚙️  Setting up database..."
python setup_full_db.py
if [ $? -ne 0 ]; then
    echo "❌ Database setup failed"
    exit 1
fi

echo ""
echo "🚀 Starting API server..."
echo "📍 Service: http://localhost:8001"
echo "📚 Swagger: http://localhost:8001/docs"
echo "📖 ReDoc: http://localhost:8001/redoc"
echo ""

python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload