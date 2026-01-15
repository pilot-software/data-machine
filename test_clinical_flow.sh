#!/bin/bash

echo "🧪 Testing Clinical AI Flow"
echo "=============================="
echo ""

API_KEY="dev-key-123"
BASE_URL="http://localhost:8001"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Step 1: Check LLM Status${NC}"
echo "─────────────────────────────"
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/api/v1/clinical-ai/status" | python3 -m json.tool
echo ""
echo ""

echo -e "${BLUE}Step 2: Test AI Diagnosis (Viral Fever)${NC}"
echo "─────────────────────────────────────────"
echo "Symptoms: cough, headache, mild fever"
echo ""
curl -s -X POST "$BASE_URL/api/v1/clinical-ai/diagnose" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "symptoms": ["cough", "headache", "mild fever"],
    "patient_age": 35,
    "patient_gender": "M",
    "location": "Mumbai",
    "duration": "3 days"
  }' | python3 -m json.tool
echo ""
echo ""

echo -e "${BLUE}Step 3: Verify Database Integration${NC}"
echo "────────────────────────────────────────"
echo "✓ ICD-10 codes: $(psql -U samirkolhe -d medical_library -t -c 'SELECT COUNT(*) FROM icd10_codes;' 2>/dev/null | xargs)"
echo "✓ SNOMED brands: $(psql -U samirkolhe -d medical_library -t -c 'SELECT COUNT(*) FROM snomed_brands;' 2>/dev/null | xargs)"
echo "✓ SNOMED generics: $(psql -U samirkolhe -d medical_library -t -c 'SELECT COUNT(*) FROM snomed_generics;' 2>/dev/null | xargs)"
echo "✓ SNOMED suppliers: $(psql -U samirkolhe -d medical_library -t -c 'SELECT COUNT(*) FROM snomed_suppliers;' 2>/dev/null | xargs)"
echo ""

echo -e "${GREEN}✅ Flow Test Complete${NC}"
