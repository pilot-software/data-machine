#!/bin/bash
# Quick ETL runner script

set -e

echo "🚀 Starting Drug Database ETL Pipeline..."

# Setup database schema (first time only)
if [ "$1" == "--setup" ]; then
    echo "📊 Setting up database schema..."
    psql -d hms_terminology -f setup_drug_db.sql
    echo "✅ Schema created"
fi

# Run ETL
echo "🔄 Running ETL pipeline..."
python etl_drug_pipeline.py

echo "✅ ETL completed successfully!"
echo ""
echo "🎯 Next steps:"
echo "  1. Start API: python -m uvicorn app.main:app --reload"
echo "  2. Test: curl http://localhost:8001/api/v1/drugs/search?query=crocin"
echo "  3. Docs: http://localhost:8001/docs"
