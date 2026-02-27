#!/bin/bash
# Import HMS Database from SQL file

set -e

# Load .env if present to allow DATABASE_URL-based defaults
if [ -f ".env" ]; then
    set -a
    # shellcheck disable=SC1091
    . ./.env
    set +a
fi

DEFAULT_DB_USER=$(whoami)
PARSED_DB_USER=""
PARSED_DB_NAME=""

if [ -n "${DATABASE_URL:-}" ]; then
    PARSED_DB_USER=$(echo "$DATABASE_URL" | sed -E 's#^[^:]+://([^:/@]+).*#\1#')
    PARSED_DB_NAME=$(echo "$DATABASE_URL" | sed -E 's#.*/([^/?]+)(\?.*)?$#\1#')
fi

DB_USER=${DB_USER:-${PARSED_DB_USER:-$DEFAULT_DB_USER}}
DB_NAME=${DB_NAME:-${PARSED_DB_NAME:-medical_library}}

# If configured DB user cannot connect, fall back to local user.
if ! psql -U "$DB_USER" -d postgres -c "SELECT 1;" >/dev/null 2>&1; then
    if [ "$DB_USER" != "$DEFAULT_DB_USER" ]; then
        echo "⚠ Could not connect as '$DB_USER'. Falling back to '$DEFAULT_DB_USER'."
        DB_USER="$DEFAULT_DB_USER"
    fi
fi

echo "=========================================="
echo "HMS Database Import"
echo "=========================================="
echo ""

# Check if dump provided
if [ -z "$1" ]; then
    echo "Usage: ./import_database.sh <archive.tar.gz|dump_file> [--recreate]"
    echo ""
    echo "Example:"
    echo "  ./import_database.sh database_dumps/hms_database_20250114.tar.gz"
    echo "  ./import_database.sh database_dumps/medical_library_cleaned_20260118_183641.tar.gz"
    echo ""
    exit 1
fi

ARCHIVE=$1
RECREATE_DB=false
if [ "${2:-}" = "--recreate" ]; then
    RECREATE_DB=true
fi

if [ ! -f "$ARCHIVE" ]; then
    echo "❌ File not found: $ARCHIVE"
    exit 1
fi

echo "Archive: $ARCHIVE"
echo "Size: $(du -h $ARCHIVE | cut -f1)"
echo "DB User: $DB_USER"
echo "DB Name: $DB_NAME"
echo ""

FILE_TYPE=$(file -b "$ARCHIVE")

# Create database if not exists
echo ""
echo "1. Setting up database..."
DB_EXISTS=$(psql -U $DB_USER -lqt | cut -d \| -f 1 | grep -w $DB_NAME | wc -l)
if [ $DB_EXISTS -eq 0 ]; then
    createdb -U $DB_USER $DB_NAME
    echo "   ✓ Database created"
else
    echo "   ⚠ Database already exists"
    if [ "$RECREATE_DB" = true ]; then
        dropdb -U $DB_USER $DB_NAME
        createdb -U $DB_USER $DB_NAME
        echo "   ✓ Database recreated (--recreate)"
    elif [ -t 0 ]; then
        read -p "   Drop and recreate? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            dropdb -U $DB_USER $DB_NAME
            createdb -U $DB_USER $DB_NAME
            echo "   ✓ Database recreated"
        fi
    else
        echo "   ⚠ Non-interactive shell detected. Keeping existing database."
    fi
fi

if [[ "$FILE_TYPE" == *"PostgreSQL custom database dump"* ]]; then
    echo ""
    echo "2. Importing PostgreSQL custom dump..."
    set +e
    if [ "$RECREATE_DB" = true ]; then
        pg_restore -U $DB_USER -d $DB_NAME --no-owner --no-privileges "$ARCHIVE"
    else
        pg_restore -U $DB_USER -d $DB_NAME --clean --if-exists --no-owner --no-privileges "$ARCHIVE"
    fi
    RESTORE_EXIT=$?
    set -e

    # Some dumps contain a small number of orphan brand rows and fail while
    # creating the FK at the end. Clean and re-apply the FK deterministically.
    ORPHAN_COUNT=$(psql -U $DB_USER -d $DB_NAME -t -A -c "SELECT COUNT(*) FROM snomed_brands b LEFT JOIN snomed_generics g ON b.generic_id = g.snomed_id WHERE b.generic_id IS NOT NULL AND g.snomed_id IS NULL;")
    if [ "${ORPHAN_COUNT:-0}" -gt 0 ]; then
        echo "   ⚠ Found $ORPHAN_COUNT orphan SNOMED brand rows; removing before FK validation..."
        psql -U $DB_USER -d $DB_NAME -c "DELETE FROM snomed_brands b WHERE b.generic_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM snomed_generics g WHERE g.snomed_id = b.generic_id);" > /dev/null
    fi

    psql -U $DB_USER -d $DB_NAME << 'EOF' > /dev/null
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'snomed_brands_generic_id_fkey'
    ) THEN
        ALTER TABLE public.snomed_brands
            ADD CONSTRAINT snomed_brands_generic_id_fkey
            FOREIGN KEY (generic_id)
            REFERENCES public.snomed_generics(snomed_id);
    END IF;
END $$;
EOF

    if [ $RESTORE_EXIT -ne 0 ]; then
        echo "   ⚠ pg_restore reported warnings; post-restore cleanup completed."
    fi
    echo "   ✓ Custom dump imported"
else
    # Extract archive
    echo ""
    echo "2. Extracting archive..."
    TEMP_DIR=$(mktemp -d)
    tar -xzf $ARCHIVE -C $TEMP_DIR
    echo "   ✓ Extracted to $TEMP_DIR"

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
fi

# Verify import
echo ""
echo "5. Verifying import..."
VERIFY_SQL="SELECT 'ICD-10 Codes: ' || COUNT(*) FROM icd10_codes
UNION ALL
SELECT 'SNOMED Brands: ' || COUNT(*) FROM snomed_brands
UNION ALL
SELECT 'SNOMED Generics: ' || COUNT(*) FROM snomed_generics;"
psql -U $DB_USER -d $DB_NAME -t -A -c "$VERIFY_SQL" | while read line; do
    echo "   $line"
done

echo ""
echo "=========================================="
echo "✅ Import Complete!"
echo "=========================================="
echo ""
echo "Database ready to use!"
echo ""
echo "Start server: ./start.sh"
echo ""
