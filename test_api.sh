#!/bin/bash

echo "🧪 Testing HMS Terminology API"
echo ""

# Check if server is running
if ! curl -s http://localhost:8001/api/v1/health > /dev/null 2>&1; then
    echo "❌ Server not running. Start with: ./start.sh"
    exit 1
fi

echo "✅ Server is running"
echo ""

# Test endpoints
echo "📋 Testing Endpoints..."
echo ""

# Health
echo "1️⃣  Health Check"
curl -s http://localhost:8001/api/v1/health | jq .
echo ""

# ICD Search
echo "2️⃣  ICD Search (diabetes)"
curl -s "http://localhost:8001/api/v1/icd10/search?q=diabetes&limit=3" | jq .
echo ""

# ICD Search with systems
echo "3️⃣  ICD Search (fever, both systems)"
curl -s "http://localhost:8001/api/v1/icd10/search?q=fever&systems=icd10,icd11&limit=2" | jq .
echo ""

# Chapters
echo "4️⃣  Get Chapters"
curl -s http://localhost:8001/api/v1/icd10/chapters | jq '.chapters | length'
echo ""

# Drug Search
echo "5️⃣  Drug Search (metformin)"
curl -s "http://localhost:8001/api/v1/drugs/search?q=metformin" | jq '.total'
echo ""

# AB-HBP Search
echo "6️⃣  AB-HBP Search (surgery)"
curl -s "http://localhost:8001/api/v1/abhbp/search?q=surgery&limit=2" | jq .
echo ""

echo "✅ All tests completed!"
echo ""
echo "📚 Full API docs: http://localhost:8001/docs"
