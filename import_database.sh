#!/bin/bash
# Import HMS Database from SQL file

set -e

DB_USER=${DB_USER:-samirkolhe}
DB_NAME=${DB_NAME:-medical_library}

echo "=========================================="
echo "HMS Database Import"
echo "=========================================="
echo ""

# Check if archive provided
if [ -z "$1" ]; then
    echo "Usage: ./import_database.sh <archive.tar.gz>"
    echo ""
    echo "Example:"
    echo "  ./import_database.sh database_dumps/hms_database_20250114.tar.gz"
    echo ""
    exit 1
fi

ARCHIVE=$1

if [ ! -f "$ARCHIVE" ]; then
    echo "❌ File not found: $ARCHIVE"
    exit 1
fi

echo "Archive: $ARCHIVE"
echo "Size: $(du -h $ARCHIVE | cut -f1)"
echo ""

# Extract archive
echo "1. Extracting archive..."
TEMP_DIR=$(mktemp -d)
tar -xzf $ARCHIVE -C $TEMP_DIR
echo "   ✓ Extracted to $TEMP_DIR"

# Create database if not exists
echo ""
echo "2. Setting up database..."
DB_EXISTS=$(psql -U $DB_USER -lqt | cut -d \| -f 1 | grep -w $DB_NAME | wc -l)
if [ $DB_EXISTS -eq 0 ]; then
    createdb -U $DB_USER $DB_NAME
    echo "   ✓ Database created"
else
    echo "   ⚠ Database already exists"
    read -p "   Drop and recreate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        dropdb -U $DB_USER $DB_NAME
        createdb -U $DB_USER $DB_NAME
        echo "   ✓ Database recreated"
    fi
fi

# Import schema
echo ""
echo "3. Importing schema..."
psql -U $DB_USER -d $DB_NAME -f $TEMP_DIR/schema.sql > /dev/null 2>&1
echo "   ✓ Schema imported"

# Import data
echo ""
echo "4. Importing data..."

if [ -f $TEMP_DIR/icd10_codes.sql ]; then
    psql -U $DB_USER -d $DB_NAME -f $TEMP_DIR/icd10_codes.sql > /dev/null 2>&1
    echo "   ✓ ICD-10 codes imported"
fi

if [ -f $TEMP_DIR/snomed_core.sql ]; then
    psql -U $DB_USER -d $DB_NAME -f $TEMP_DIR/snomed_core.sql > /dev/null 2>&1
    echo "   ✓ SNOMED core data imported"
fi

if [ -f $TEMP_DIR/snomed_extended.sql ]; then
    psql -U $DB_USER -d $DB_NAME -f $TEMP_DIR/snomed_extended.sql > /dev/null 2>&1
    echo "   ✓ SNOMED extended data imported"
fi

# Cleanup
rm -rf $TEMP_DIR

# Verify import
echo ""
echo "5. Verifying import..."
psql -U $DB_USER -d $DB_NAME -t << 'EOF' | while read line; do
    echo "   $line"
done
SELECT 'ICD-10 Codes: ' || COUNT(*) FROM icd10_codes
UNION ALL
SELECT 'SNOMED Brands: ' || COUNT(*) FROM snomed_brands
UNION ALL
SELECT 'SNOMED Generics: ' || COUNT(*) FROM snomed_generics;
EOF

echo ""
echo "=========================================="
echo "✅ Import Complete!"
echo "=========================================="
echo ""
echo "Database ready to use!"
echo ""
echo "Start server: ./start.sh"
echo ""
