#!/bin/bash
# Export HMS Database to SQL file (for easy sharing)

set -e

DB_USER=${DB_USER:-samirkolhe}
DB_NAME=${DB_NAME:-medical_library}
OUTPUT_DIR="database_dumps"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=========================================="
echo "HMS Database Export"
echo "=========================================="
echo ""

# Create output directory
mkdir -p $OUTPUT_DIR

echo "Exporting database to SQL..."
echo ""

# Export schema only (small)
echo "1. Exporting schema..."
pg_dump -U $DB_USER -d $DB_NAME --schema-only \
  -f $OUTPUT_DIR/schema.sql
echo "   ✓ schema.sql ($(du -h $OUTPUT_DIR/schema.sql | cut -f1))"

# Export data tables separately
echo ""
echo "2. Exporting data tables..."

# ICD codes
pg_dump -U $DB_USER -d $DB_NAME \
  --data-only --table=icd10_codes \
  -f $OUTPUT_DIR/icd10_codes.sql
echo "   ✓ icd10_codes.sql ($(du -h $OUTPUT_DIR/icd10_codes.sql | cut -f1))"

# SNOMED tables
pg_dump -U $DB_USER -d $DB_NAME \
  --data-only \
  --table=snomed_brands \
  --table=snomed_generics \
  --table=snomed_suppliers \
  --table=snomed_substances \
  --table=snomed_products \
  --table=snomed_drug_forms \
  --table=snomed_routes \
  -f $OUTPUT_DIR/snomed_core.sql
echo "   ✓ snomed_core.sql ($(du -h $OUTPUT_DIR/snomed_core.sql | cut -f1))"

# Extended data (optional)
pg_dump -U $DB_USER -d $DB_NAME \
  --data-only \
  --table=snomed_drug_hierarchy \
  --table=snomed_drug_dosages \
  --table=snomed_drug_classes \
  --table=snomed_drug_definitions \
  -f $OUTPUT_DIR/snomed_extended.sql 2>/dev/null || echo "   ⚠ Extended tables not found (optional)"

if [ -f $OUTPUT_DIR/snomed_extended.sql ]; then
    echo "   ✓ snomed_extended.sql ($(du -h $OUTPUT_DIR/snomed_extended.sql | cut -f1))"
fi

# Create compressed archive
echo ""
echo "3. Creating compressed archive..."
cd $OUTPUT_DIR
tar -czf hms_database_$TIMESTAMP.tar.gz *.sql
cd ..

ARCHIVE_SIZE=$(du -h $OUTPUT_DIR/hms_database_$TIMESTAMP.tar.gz | cut -f1)

echo "   ✓ hms_database_$TIMESTAMP.tar.gz ($ARCHIVE_SIZE)"

# Cleanup individual SQL files
rm $OUTPUT_DIR/*.sql

echo ""
echo "=========================================="
echo "✅ Export Complete!"
echo "=========================================="
echo ""
echo "Archive: $OUTPUT_DIR/hms_database_$TIMESTAMP.tar.gz"
echo "Size: $ARCHIVE_SIZE"
echo ""
echo "Share this file with your team!"
echo ""
echo "To import on another machine:"
echo "  ./import_database.sh $OUTPUT_DIR/hms_database_$TIMESTAMP.tar.gz"
echo ""
