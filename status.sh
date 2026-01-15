#!/bin/bash
# Check HMS Terminology Service Status

echo "Checking HMS Terminology Service..."
echo ""

# Check if process is running
if pgrep -f "uvicorn app.main:app" > /dev/null; then
    echo "✅ Server is running"
    
    # Check if responding
    if curl -s http://localhost:8001/api/v1/health > /dev/null 2>&1; then
        echo "✅ Server is responding"
        
        # Get stats
        echo ""
        echo "📊 Database Statistics:"
        psql -U ${DB_USER:-samirkolhe} -d ${DB_NAME:-medical_library} -t << 'EOF' 2>/dev/null
SELECT '  ICD-10 Codes: ' || COUNT(*) FROM icd10_codes
UNION ALL
SELECT '  SNOMED Brands: ' || COUNT(*) FROM snomed_brands
UNION ALL
SELECT '  Antibiotics: ' || COUNT(*) FROM snomed_drug_classes WHERE is_antibiotic;
EOF
        
        echo ""
        echo "🌐 Endpoints:"
        echo "  API Docs: http://localhost:8001/docs"
        echo "  Health:   http://localhost:8001/api/v1/health"
        
    else
        echo "❌ Server not responding"
    fi
else
    echo "❌ Server is not running"
    echo ""
    echo "Start with: ./start.sh"
fi
