#!/bin/bash
# Quick setup script for AB-HBP integration

set -e

echo "🏥 Setting up Ayushman Bharat HBP..."

# 1. Setup database
echo "📊 Creating database tables..."
psql -d hms_terminology -f scripts/setup_drug_db.sql

# 2. Download data
echo "📥 Downloading AB-HBP data..."
python scripts/etl/download_abhbp_data.py

# 3. Load data
echo "💾 Loading data into database..."
python scripts/etl/load_abhbp_data.py

echo "✅ AB-HBP setup complete!"
echo "🚀 Test API: curl http://localhost:8001/api/v1/abhbp/search?q=surgery"
