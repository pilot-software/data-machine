#!/bin/bash
# Setup SNOMED CT RF2 Extended Data (Hierarchies, Definitions, Dosages)

set -e

echo "=========================================="
echo "SNOMED CT RF2 Extended Data Setup"
echo "=========================================="

# Check if RF2 folder exists
if [ ! -d "SnomedCT_IndiaDrugExtensionRF2_PRODUCTION_IN1000189_20251219T120000Z" ]; then
    echo "❌ RF2 folder not found!"
    echo "Please ensure SnomedCT_IndiaDrugExtensionRF2_PRODUCTION_IN1000189_20251219T120000Z exists"
    exit 1
fi

echo "✓ RF2 folder found"

# Create logs directory
mkdir -p logs

# Run ETL
echo ""
echo "Loading RF2 extended data..."
python3 scripts/etl/load_snomed_rf2_extended.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ RF2 Extended Data Loaded Successfully!"
    echo "=========================================="
    echo ""
    echo "New Features Available:"
    echo "  • Drug hierarchies (show all antibiotics)"
    echo "  • Clinical definitions"
    echo "  • Precise dosage information"
    echo "  • Drug classifications"
    echo ""
    echo "New API Endpoints:"
    echo "  GET /api/v1/snomed/extended/drug-classes"
    echo "  GET /api/v1/snomed/extended/antibiotics"
    echo "  GET /api/v1/snomed/extended/by-class/{class}"
    echo "  GET /api/v1/snomed/extended/definition/{id}"
    echo "  GET /api/v1/snomed/extended/dosage/{id}"
    echo "  GET /api/v1/snomed/extended/hierarchy/{id}"
    echo ""
else
    echo "❌ RF2 loading failed. Check logs/snomed_etl.log"
    exit 1
fi
