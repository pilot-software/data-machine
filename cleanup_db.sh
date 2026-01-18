#!/bin/bash
# Cleanup unused database tables

set -e

echo "🧹 Cleaning up unused database tables..."

# Execute cleanup SQL
psql -U samirkolhe -d medical_library -f scripts/cleanup_unused_tables.sql

echo "✅ Cleanup completed successfully"
echo ""
echo "Removed tables:"
echo "  - loinc (Lab test codes)"
echo "  - symptoms_master (Unused symptoms)"
echo "  - abhbp_procedures (Ayushman Bharat)"
echo "  - snomed_drug_forms (Unused)"
echo "  - snomed_routes (Unused)"
echo "  - snomed_etl_log (ETL logs)"
echo ""
echo "Core tables retained:"
echo "  ✓ icd10_codes"
echo "  ✓ snomed_brands"
echo "  ✓ snomed_generics"
echo "  ✓ snomed_products"
echo "  ✓ snomed_suppliers"
echo "  ✓ snomed_substances"
