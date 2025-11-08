#!/bin/bash

echo "🚀 Starting HMS Terminology Service..."
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Run: ./setup.sh first"
    exit 1
fi

# Activate venv
source venv/bin/activate
PYTHON_CMD="python"

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
$PYTHON_CMD scripts/setup_full_db.py
if [ $? -ne 0 ]; then
    echo "❌ Database setup failed"
    exit 1
fi

echo "💊 Setting up drug tables..."
psql -d hms_terminology -f scripts/setup_drug_db.sql > /dev/null 2>&1

echo "📦 Loading sample drug data..."
$PYTHON_CMD scripts/etl/load_sample_data.py
if [ $? -ne 0 ]; then
    echo "⚠️  Sample data loading failed (continuing anyway)"
fi

echo "🏥 Loading AB-HBP data..."
psql -d hms_terminology -c "ALTER TABLE abhbp_procedures ALTER COLUMN procedure_type TYPE TEXT;" > /dev/null 2>&1
if [ -f "data/abhbp_packages.csv" ]; then
    $PYTHON_CMD scripts/etl/load_abhbp_data.py
    if [ $? -eq 0 ]; then
        echo "✅ AB-HBP data loaded"
    else
        echo "⚠️  AB-HBP loading failed (continuing anyway)"
    fi
else
    echo "⚠️  AB-HBP data not found, run: $PYTHON_CMD scripts/etl/download_abhbp_data.py"
fi

echo ""
echo "🚀 Starting API server..."
echo "📍 Service: http://localhost:8001"
echo "📚 Swagger: http://localhost:8001/docs"
echo "📖 ReDoc: http://localhost:8001/redoc"
echo ""

$PYTHON_CMD -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
