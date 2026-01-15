#!/bin/bash
# Comprehensive Test Suite for HMS Terminology Service

set -e

API_KEY="dev-key-123"
BASE_URL="http://localhost:8001"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "HMS Terminology Service - Test Suite"
echo "=========================================="
echo ""

PASSED=0
FAILED=0

# Helper function
test_endpoint() {
    local name=$1
    local url=$2
    local expected=$3
    
    echo -n "Testing $name... "
    
    response=$(curl -s -H "X-API-Key: $API_KEY" "$url")
    
    if echo "$response" | grep -q "$expected"; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "  Expected: $expected"
        echo "  Got: $response"
        ((FAILED++))
        return 1
    fi
}

# 1. Health Check
echo -e "${BLUE}1. Health Check${NC}"
test_endpoint "Server Health" "$BASE_URL/api/v1/health" "status"
echo ""

# 2. ICD Codes
echo -e "${BLUE}2. ICD-10 Codes${NC}"
test_endpoint "ICD Search - Diabetes" "$BASE_URL/api/v1/icd/search?q=diabetes" "E11"
test_endpoint "ICD Get Code" "$BASE_URL/api/v1/icd/E11" "Type 2 diabetes"
echo ""

# 3. SNOMED Drug Search
echo -e "${BLUE}3. SNOMED Drug Search${NC}"
test_endpoint "Drug Search - Paracetamol" "$BASE_URL/api/v1/snomed/search?q=paracetamol" "brand_name"
test_endpoint "Drug Autocomplete" "$BASE_URL/api/v1/snomed/autocomplete?q=para" "paracetamol"
test_endpoint "SNOMED Stats" "$BASE_URL/api/v1/snomed/stats" "total_brands"
echo ""

# 4. Drug Classifications
echo -e "${BLUE}4. Drug Classifications (RF2 Extended)${NC}"
test_endpoint "Drug Classes" "$BASE_URL/api/v1/snomed/extended/drug-classes" "antibiotics"
test_endpoint "Get Antibiotics" "$BASE_URL/api/v1/snomed/extended/antibiotics?page_size=5" "brand_name"
test_endpoint "Get Analgesics" "$BASE_URL/api/v1/snomed/extended/by-class/analgesic?page_size=5" "brand_name"
echo ""

# 5. AI Clinical Assistant
echo -e "${BLUE}5. AI Clinical Assistant${NC}"

# Test structured diagnosis
echo -n "Testing AI Diagnosis (Structured)... "
response=$(curl -s -X POST -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"symptoms":["fever","cough"],"patient_age":35,"patient_gender":"M"}' \
  "$BASE_URL/api/v1/clinical-ai/diagnose")

if echo "$response" | grep -q "llm_provider"; then
    echo -e "${GREEN}✓ PASSED${NC}"
    echo "  Provider: $(echo $response | grep -o '"llm_provider":"[^"]*"' | cut -d'"' -f4)"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    ((FAILED++))
fi

# Test natural language diagnosis
echo -n "Testing AI Diagnosis (Natural Language)... "
response=$(curl -s -X POST -H "X-API-Key: $API_KEY" \
  "$BASE_URL/api/v1/clinical-ai/diagnose-text?prompt=stomach%20pain%20and%20fever")

if echo "$response" | grep -q "diagnosis_suggestions"; then
    echo -e "${GREEN}✓ PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    ((FAILED++))
fi

# Test LLM status
test_endpoint "LLM Status" "$BASE_URL/api/v1/clinical-ai/status" "provider"
echo ""

# 6. Database Statistics
echo -e "${BLUE}6. Database Statistics${NC}"
echo "Querying database..."

DB_USER=${DB_USER:-samirkolhe}
DB_NAME=${DB_NAME:-medical_library}

psql -U $DB_USER -d $DB_NAME -t << 'EOF' 2>/dev/null | while read line; do
    echo "  $line"
done
SELECT 'ICD-10 Codes: ' || COUNT(*) FROM icd10_codes
UNION ALL
SELECT 'SNOMED Brands: ' || COUNT(*) FROM snomed_brands
UNION ALL
SELECT 'SNOMED Generics: ' || COUNT(*) FROM snomed_generics
UNION ALL
SELECT 'SNOMED Suppliers: ' || COUNT(*) FROM snomed_suppliers
UNION ALL
SELECT 'Antibiotics: ' || COUNT(*) FROM snomed_drug_classes WHERE is_antibiotic
UNION ALL
SELECT 'Analgesics: ' || COUNT(*) FROM snomed_drug_classes WHERE is_analgesic
UNION ALL
SELECT 'Drug Hierarchies: ' || COUNT(*) FROM snomed_drug_hierarchy
UNION ALL
SELECT 'Dosage Records: ' || COUNT(*) FROM snomed_drug_dosages;
EOF

echo ""

# 7. Performance Test
echo -e "${BLUE}7. Performance Test${NC}"
echo -n "Testing response time (10 requests)... "

total_time=0
for i in {1..10}; do
    start=$(date +%s%N)
    curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/api/v1/snomed/search?q=paracetamol" > /dev/null
    end=$(date +%s%N)
    elapsed=$((($end - $start) / 1000000))
    total_time=$(($total_time + $elapsed))
done

avg_time=$(($total_time / 10))

if [ $avg_time -lt 100 ]; then
    echo -e "${GREEN}✓ PASSED${NC} (avg: ${avg_time}ms)"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ SLOW${NC} (avg: ${avg_time}ms, expected <100ms)"
fi

echo ""

# 8. API Documentation
echo -e "${BLUE}8. API Documentation${NC}"
test_endpoint "OpenAPI Docs" "$BASE_URL/docs" "Swagger"
echo ""

# Summary
echo "=========================================="
echo -e "${BLUE}Test Summary${NC}"
echo "=========================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "🎉 Your HMS Terminology Service is fully operational!"
    echo ""
    echo "📖 API Documentation: $BASE_URL/docs"
    echo "🔑 API Key: $API_KEY"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo ""
    echo "Check logs: tail -f logs/server.log"
    echo ""
    exit 1
fi
