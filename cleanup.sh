#!/bin/bash

# 🧹 Cleanup Script - Remove Redundant Files
# This script removes deprecated, duplicate, and unnecessary files

echo "🧹 Starting cleanup of redundant files..."
echo ""

# Create backup directory
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "📦 Backup directory created: $BACKUP_DIR"
echo ""

# Function to safely remove file/directory
safe_remove() {
    if [ -e "$1" ]; then
        mv "$1" "$BACKUP_DIR/"
        echo "✅ Moved: $1"
    fi
}

echo "🗑️  Removing deprecated files..."
# Deprecated code files
safe_remove "app/api/drug_endpoints.py.deprecated"
safe_remove "scripts/deprecated_start.sh"
safe_remove "scripts/deprecated_test_apis.sh"

echo ""
echo "📄 Removing redundant documentation..."
# Redundant docs (keeping only essential ones)
safe_remove "docs/API_ENDPOINTS_V1.md"           # Duplicate of API.md
safe_remove "docs/FINAL_API_ENDPOINTS.md"        # Duplicate of API.md
safe_remove "docs/SERVICE_COMMANDS.md"           # Info in README.md
safe_remove "docs/SETUP_GUIDE.md"                # Info in DEPLOYMENT.md
safe_remove "docs/AI_ENHANCED_PRODUCT_SPEC.md"   # Old spec document
safe_remove "docs/README_DRUG_ETL.md"            # Internal ETL docs
safe_remove "docs/CRON_SETUP.md"                 # Advanced feature, rarely used
safe_remove "docs/OPENSOURCE_DATA_SOURCES.md"    # Internal data source info
safe_remove "docs/DATA_SOURCES.md"               # Duplicate info

# Keep these important docs:
# - docs/SNOMED_INTEGRATION.md (technical reference)
# - docs/SNOMED_MIGRATION_GUIDE.md (migration guide)
# - docs/ABHBP_INTEGRATION.md (integration guide)
# - docs/AUTH_GUIDE.md (security reference)

echo ""
echo "🔧 Removing redundant scripts..."
# Redundant scripts
safe_remove "scripts/unified_api.py"             # Old unified API
safe_remove "scripts/code_detector.py"           # Development tool
safe_remove "scripts/config.json"                # Old config
safe_remove "scripts/HMS_Terminology_API.postman_collection.json"  # Use Swagger instead

echo ""
echo "📊 Removing old SQL setup files..."
# Old SQL files (database now uses dump import)
safe_remove "scripts/setup_drug_db.sql"
safe_remove "scripts/setup_prescription_tracking.sql"
safe_remove "scripts/setup_audit_tables.sql"
safe_remove "scripts/add_r05_children.sql"

echo ""
echo "🗂️  Removing redundant ETL scripts..."
# Keep only essential ETL scripts
safe_remove "scripts/etl/download_from_azure.py"      # Azure specific
safe_remove "scripts/etl/download_opensource_data.py" # Not needed
safe_remove "scripts/etl/download_real_data.py"       # Not needed
safe_remove "scripts/etl/download_expanded_data.py"   # Not needed
safe_remove "scripts/etl/load_sample_data.py"         # Use database dump
safe_remove "scripts/etl/load_expanded_data.py"       # Use database dump
safe_remove "scripts/etl/load_real_data.py"           # Use database dump
safe_remove "scripts/etl/load_indications.py"         # Use database dump
safe_remove "scripts/etl/etl_drug_pipeline.py"        # Use database dump

# Keep these ETL scripts:
# - scripts/etl/load_snomed_data.py (core SNOMED loading)
# - scripts/etl/load_snomed_rf2_extended.py (extended data)
# - scripts/etl/download_icd10_complete.py (ICD-10 updates)
# - scripts/etl/load_abhbp_data.py (ABHBP integration)
# - scripts/etl/download_abhbp_data.py (ABHBP data)

echo ""
echo "🔄 Removing redundant shell scripts..."
safe_remove "scripts/run_etl.sh"                 # Use database dump
safe_remove "scripts/setup_snomed.sh"            # Use database dump
safe_remove "scripts/setup_snomed_rf2.sh"        # Use database dump
safe_remove "scripts/setup_abhbp.sh"             # Use database dump
safe_remove "scripts/test_snomed_api.sh"         # Use test_all.sh

# Keep these shell scripts:
# - scripts/cron/* (for scheduled tasks)

echo ""
echo "📝 Removing redundant root markdown files..."
safe_remove "GIT_GUIDE.md"                       # Basic git info
safe_remove "PRODUCTION_PIPELINE_ARCHITECTURE.md" # Too detailed for new users

# Keep these root markdown files:
# - README.md (main entry point)
# - API.md (API documentation)
# - DEPLOYMENT.md (deployment guide)
# - WORKFLOW.md (usage patterns)
# - LLM_SETUP_GUIDE.md (AI setup)
# - ONBOARDING_GUIDE.md (new engineer guide)

echo ""
echo "🧪 Removing old test files..."
safe_remove "tests/test_abhbp_direct.py"         # Duplicate test

# Keep these test files:
# - tests/test_api_consolidated.py (main API tests)
# - tests/test_abhbp_api.py (ABHBP tests)
# - tests/test_architecture.py (architecture tests)

echo ""
echo "📦 Removing data files (use database dump instead)..."
# Data files should be in database, not in repo
safe_remove "data/abhbp_packages.csv"
safe_remove "data/abhbp_packages.xlsx"
safe_remove "data/drug_indications.csv"
safe_remove "data/icd10_full_processed.csv"
safe_remove "data/icd10_full_processed.json"
safe_remove "data/icd11_who_api.json"
safe_remove "data/sample_indian_drugs.csv"

# Note: data/real/ and data/opensource/ are already in .gitignore

echo ""
echo "✅ Cleanup completed!"
echo ""
echo "📊 Summary:"
echo "   - All removed files backed up to: $BACKUP_DIR"
echo "   - To restore: mv $BACKUP_DIR/* ./"
echo "   - To permanently delete backup: rm -rf $BACKUP_DIR"
echo ""
echo "📁 Remaining structure:"
echo "   ✅ app/ - Core application code"
echo "   ✅ scripts/etl/ - Essential ETL scripts (5 files)"
echo "   ✅ scripts/cron/ - Scheduled tasks"
echo "   ✅ tests/ - Test files (3 files)"
echo "   ✅ docs/ - Essential docs (4 files)"
echo "   ✅ Root scripts - Daily use (8 files)"
echo "   ✅ Root docs - Main guides (6 files)"
echo ""
echo "🎉 Project is now cleaner and easier to navigate!"
