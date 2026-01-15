#!/bin/bash

echo "🩺 Natural Language Diagnosis API - Test Examples"
echo "=================================================="
echo ""

API_KEY="dev-key-123"
BASE_URL="http://localhost:8001/api/v1/clinical-ai"

# Test 1: UTI Symptoms
echo "Test 1: UTI Symptoms"
echo "--------------------"
echo "Prompt: frequent urination burning while passing urine lower abdominal pain female 32 years"
echo ""
curl -s -X POST "$BASE_URL/diagnose-text?prompt=frequent%20urination%20burning%20while%20passing%20urine%20lower%20abdominal%20pain%20female%2032%20years" \
  -H "X-API-Key: $API_KEY" | python3 -m json.tool
echo ""
echo ""

# Test 2: Common Cold
echo "Test 2: Common Cold"
echo "-------------------"
echo "Prompt: having cough and cold since 2 days"
echo ""
curl -s -X POST "$BASE_URL/diagnose-text?prompt=having%20cough%20and%20cold%20since%202%20days" \
  -H "X-API-Key: $API_KEY" | python3 -m json.tool
echo ""
echo ""

# Test 3: Fever
echo "Test 3: Fever Symptoms"
echo "----------------------"
echo "Prompt: high fever body ache headache for 3 days"
echo ""
curl -s -X POST "$BASE_URL/diagnose-text?prompt=high%20fever%20body%20ache%20headache%20for%203%20days" \
  -H "X-API-Key: $API_KEY" | python3 -m json.tool
echo ""
echo ""

# Test 4: Diabetes Symptoms
echo "Test 4: Diabetes Symptoms"
echo "-------------------------"
echo "Prompt: excessive thirst frequent urination weight loss fatigue"
echo ""
curl -s -X POST "$BASE_URL/diagnose-text?prompt=excessive%20thirst%20frequent%20urination%20weight%20loss%20fatigue" \
  -H "X-API-Key: $API_KEY" | python3 -m json.tool
echo ""
echo ""

echo "✅ Tests Complete"
echo ""
echo "API Documentation:"
echo "  Endpoint: POST /api/v1/clinical-ai/diagnose-text"
echo "  Parameter: prompt (URL encoded string)"
echo "  Header: X-API-Key: dev-key-123"
echo ""
echo "Example Usage:"
echo "  curl -X POST \"$BASE_URL/diagnose-text?prompt=YOUR_SYMPTOMS_HERE\" \\"
echo "    -H \"X-API-Key: dev-key-123\""
