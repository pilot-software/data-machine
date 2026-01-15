#!/bin/bash
# ============================================================================
# SNOMED CT API Test Script
# Tests all SNOMED endpoints
# ============================================================================

set -e

# Configuration
API_BASE="http://localhost:8001"
API_KEY="dev-key-123"
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# ============================================================================
# Helper Functions
# ============================================================================

test_endpoint() {
    local name="$1"
    local endpoint="$2"
    local expected_status="${3:-200}"
    
    echo -e "${BLUE}Testing:${NC} $name"
    
    response=$(curl -s -w "\n%{http_code}" -H "X-API-Key: $API_KEY" "$API_BASE$endpoint")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $http_code)"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC} (Expected $expected_status, got $http_code)"
        echo "$body"
        ((TESTS_FAILED++))
    fi
    echo ""
}

# ============================================================================
# Tests
# ============================================================================

echo "============================================================================"
echo "SNOMED CT API Tests"
echo "============================================================================"
echo ""

# Test 1: Statistics
test_endpoint "Get SNOMED Statistics" "/api/v1/snomed/stats"

# Test 2: Search by brand name
test_endpoint "Search by Brand Name (Crocin)" "/api/v1/snomed/search?q=crocin&page_size=5"

# Test 3: Search by generic name
test_endpoint "Search by Generic Name (Metformin)" "/api/v1/snomed/search?q=metformin&page_size=5"

# Test 4: Search by indication
test_endpoint "Search by Indication (diabetes)" "/api/v1/snomed/search?q=diabetes&page_size=5"

# Test 5: Autocomplete
test_endpoint "Autocomplete (met)" "/api/v1/snomed/autocomplete?q=met&limit=5"

# Test 6: Get brand details (using first result from search)
echo -e "${BLUE}Getting first brand ID from search...${NC}"
BRAND_ID=$(curl -s -H "X-API-Key: $API_KEY" "$API_BASE/api/v1/snomed/search?q=metformin&page_size=1" | jq -r '.results[0].snomed_id')

if [ "$BRAND_ID" != "null" ] && [ -n "$BRAND_ID" ]; then
    echo "Found brand ID: $BRAND_ID"
    test_endpoint "Get Brand Details" "/api/v1/snomed/brands/$BRAND_ID"
    
    # Test 7: Get alternatives
    test_endpoint "Get Brand Alternatives" "/api/v1/snomed/brands/$BRAND_ID/alternatives?limit=5"
else
    echo -e "${RED}Could not get brand ID for testing${NC}"
    ((TESTS_FAILED+=2))
fi
echo ""

# Test 8: Get generic details
echo -e "${BLUE}Getting first generic ID from search...${NC}"
GENERIC_ID=$(curl -s -H "X-API-Key: $API_KEY" "$API_BASE/api/v1/snomed/search?q=metformin&page_size=1" | jq -r '.results[0].generic_snomed_id')

if [ "$GENERIC_ID" != "null" ] && [ -n "$GENERIC_ID" ]; then
    echo "Found generic ID: $GENERIC_ID"
    test_endpoint "Get Generic Details" "/api/v1/snomed/generics/$GENERIC_ID"
    
    # Test 9: Get brands by generic
    test_endpoint "Get Brands by Generic" "/api/v1/snomed/generics/$GENERIC_ID/brands?page_size=5"
else
    echo -e "${RED}Could not get generic ID for testing${NC}"
    ((TESTS_FAILED+=2))
fi
echo ""

# Test 10: Get supplier details
echo -e "${BLUE}Getting first supplier ID...${NC}"
SUPPLIER_ID=$(curl -s -H "X-API-Key: $API_KEY" "$API_BASE/api/v1/snomed/search?q=metformin&page_size=1" | jq -r '.results[0].supplier_name' | head -1)

if [ "$SUPPLIER_ID" != "null" ] && [ -n "$SUPPLIER_ID" ]; then
    # Get supplier SNOMED ID from database
    echo "Found supplier: $SUPPLIER_ID"
    # Note: This test requires knowing a valid supplier SNOMED ID
    # Skipping for now as we need to query the database
    echo -e "${BLUE}Skipping supplier tests (requires database query)${NC}"
else
    echo -e "${RED}Could not get supplier for testing${NC}"
fi
echo ""

# Test 11: Pagination
test_endpoint "Search with Pagination (page 1)" "/api/v1/snomed/search?q=tablet&page=1&page_size=10"
test_endpoint "Search with Pagination (page 2)" "/api/v1/snomed/search?q=tablet&page=2&page_size=10"

# Test 12: Filter active only
test_endpoint "Search Active Drugs Only" "/api/v1/snomed/search?q=metformin&filter_active=true&page_size=5"

# Test 13: Invalid brand ID (should return 404)
test_endpoint "Get Invalid Brand (404)" "/api/v1/snomed/brands/999999999999" 404

# Test 14: Invalid generic ID (should return 404)
test_endpoint "Get Invalid Generic (404)" "/api/v1/snomed/generics/999999999999" 404

# Test 15: Empty search query (should return 400)
test_endpoint "Empty Search Query (400)" "/api/v1/snomed/search?q=" 422

# ============================================================================
# Performance Tests
# ============================================================================

echo "============================================================================"
echo "Performance Tests"
echo "============================================================================"
echo ""

echo -e "${BLUE}Testing search performance (10 queries)...${NC}"
total_time=0
for i in {1..10}; do
    start=$(date +%s%N)
    curl -s -H "X-API-Key: $API_KEY" "$API_BASE/api/v1/snomed/search?q=metformin&page_size=20" > /dev/null
    end=$(date +%s%N)
    elapsed=$((($end - $start) / 1000000))
    total_time=$(($total_time + $elapsed))
    echo "Query $i: ${elapsed}ms"
done
avg_time=$(($total_time / 10))
echo -e "${GREEN}Average response time: ${avg_time}ms${NC}"

if [ $avg_time -lt 100 ]; then
    echo -e "${GREEN}✓ Performance test PASSED (< 100ms)${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Performance test FAILED (>= 100ms)${NC}"
    ((TESTS_FAILED++))
fi
echo ""

# ============================================================================
# Summary
# ============================================================================

echo "============================================================================"
echo "Test Summary"
echo "============================================================================"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo "Total: $(($TESTS_PASSED + $TESTS_FAILED))"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed ✗${NC}"
    exit 1
fi
