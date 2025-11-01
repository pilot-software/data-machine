#!/bin/bash

BASE_URL="http://127.0.0.1:8002"

echo "=== API TESTING STARTED ==="
echo ""

# Test 1: Health Check
echo "1. Testing Health Check..."
curl -s "$BASE_URL/api/v1/health" | python -m json.tool
echo ""

# Test 2: Detailed Health
echo "2. Testing Detailed Health..."
curl -s "$BASE_URL/api/v1/health/detailed" | python -m json.tool
echo ""

# Test 3: Unified Search
echo "3. Testing Unified Search..."
curl -s "$BASE_URL/api/v1/search/unified?query=diabetes&limit=3" | python -m json.tool
echo ""

# Test 4: ICD-10 Autocomplete
echo "4. Testing ICD-10 Autocomplete..."
curl -s "$BASE_URL/api/v1/autocomplete/icd10?query=diab&limit=5" | python -m json.tool
echo ""

# Test 5: ICD-10 Search
echo "5. Testing ICD-10 Search..."
curl -s "$BASE_URL/api/v1/search/icd10?query=diabetes&limit=3" | python -m json.tool
echo ""

# Test 6: Advanced ICD-10 Search
echo "6. Testing Advanced ICD-10 Search..."
curl -s "$BASE_URL/api/v1/enterprise/search/icd10/advanced?query=diabetes&limit=3" | python -m json.tool
echo ""

# Test 7: ICD-10 Chapters
echo "7. Testing ICD-10 Chapters..."
curl -s "$BASE_URL/api/v1/enterprise/chapters" | python -m json.tool | head -30
echo ""

echo "=== API TESTING COMPLETED ==="
