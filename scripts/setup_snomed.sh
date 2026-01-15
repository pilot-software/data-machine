#!/bin/bash
# ============================================================================
# SNOMED CT Indian Drug Database Setup Script
# Production-grade automated setup
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_ROOT/CommonDrugCodesForIndia_FlatFilePackage"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/snomed_setup.log"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    source "$PROJECT_ROOT/.env"
else
    echo -e "${RED}Error: .env file not found${NC}"
    exit 1
fi

# Database connection
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-hms_terminology}"
DB_USER="${DB_USER:-postgres}"

# ============================================================================
# Functions
# ============================================================================

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if data directory exists
    if [ ! -d "$DATA_DIR" ]; then
        error "Data directory not found: $DATA_DIR"
    fi
    
    # Check if required files exist
    local required_files=(
        "BrandMaster.txt"
        "GenericMaster.txt"
        "ProductMaster.txt"
        "SupplierMaster.txt"
        "SubstanceMaster.txt"
        "DrugFormMaster.txt"
        "RouteOfAdministrationMaster.txt"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$DATA_DIR/$file" ]; then
            error "Required file not found: $file"
        fi
    done
    
    # Check PostgreSQL connection
    if ! PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" > /dev/null 2>&1; then
        error "Cannot connect to PostgreSQL database"
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed"
    fi
    
    log "All prerequisites met ✓"
}

create_logs_dir() {
    mkdir -p "$LOG_DIR"
    log "Logs directory created: $LOG_DIR"
}

setup_database_schema() {
    log "Setting up SNOMED database schema..."
    
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -f "$SCRIPT_DIR/setup_snomed_db.sql" >> "$LOG_FILE" 2>&1
    
    if [ $? -eq 0 ]; then
        log "Database schema created successfully ✓"
    else
        error "Failed to create database schema"
    fi
}

load_data() {
    log "Loading SNOMED data (this may take 5-10 minutes)..."
    
    cd "$PROJECT_ROOT"
    
    python3 scripts/etl/load_snomed_data.py >> "$LOG_FILE" 2>&1
    
    if [ $? -eq 0 ]; then
        log "Data loaded successfully ✓"
    else
        error "Failed to load data"
    fi
}

verify_data() {
    log "Verifying data integrity..."
    
    local counts=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
        SELECT 
            (SELECT COUNT(*) FROM snomed_brands) as brands,
            (SELECT COUNT(*) FROM snomed_generics) as generics,
            (SELECT COUNT(*) FROM snomed_products) as products,
            (SELECT COUNT(*) FROM snomed_suppliers) as suppliers,
            (SELECT COUNT(*) FROM snomed_substances) as substances;
    ")
    
    info "Data counts:"
    echo "$counts" | tee -a "$LOG_FILE"
    
    # Check if materialized view exists
    local view_count=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
        SELECT COUNT(*) FROM snomed_drugs_complete;
    ")
    
    if [ "$view_count" -gt 0 ]; then
        log "Materialized view verified: $view_count records ✓"
    else
        warn "Materialized view is empty"
    fi
}

create_indexes() {
    log "Creating additional performance indexes..."
    
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
        VACUUM ANALYZE snomed_brands;
        VACUUM ANALYZE snomed_generics;
        VACUUM ANALYZE snomed_products;
        VACUUM ANALYZE snomed_suppliers;
        VACUUM ANALYZE snomed_substances;
    " >> "$LOG_FILE" 2>&1
    
    log "Indexes optimized ✓"
}

print_summary() {
    echo ""
    echo -e "${GREEN}============================================================================${NC}"
    echo -e "${GREEN}SNOMED CT Indian Drug Database Setup Complete!${NC}"
    echo -e "${GREEN}============================================================================${NC}"
    echo ""
    
    # Get statistics
    local stats=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
        SELECT 
            (SELECT COUNT(*) FROM snomed_brands WHERE active = TRUE) as active_brands,
            (SELECT COUNT(*) FROM snomed_generics) as generics,
            (SELECT COUNT(*) FROM snomed_suppliers WHERE active = TRUE) as suppliers,
            (SELECT COUNT(*) FROM snomed_substances) as substances;
    ")
    
    echo -e "${BLUE}Database Statistics:${NC}"
    echo "$stats"
    echo ""
    
    echo -e "${BLUE}API Endpoints Available:${NC}"
    echo "  • GET  /api/v1/snomed/search?q=<query>"
    echo "  • GET  /api/v1/snomed/brands/{snomed_id}"
    echo "  • GET  /api/v1/snomed/generics/{snomed_id}"
    echo "  • GET  /api/v1/snomed/brands/{snomed_id}/alternatives"
    echo "  • GET  /api/v1/snomed/suppliers/{snomed_id}"
    echo "  • GET  /api/v1/snomed/autocomplete?q=<query>"
    echo "  • GET  /api/v1/snomed/stats"
    echo ""
    
    echo -e "${BLUE}Next Steps:${NC}"
    echo "  1. Restart the API service: ./start.sh"
    echo "  2. Test SNOMED endpoints: curl -H 'X-API-Key: dev-key-123' http://localhost:8001/api/v1/snomed/stats"
    echo "  3. View API docs: http://localhost:8001/docs"
    echo ""
    
    echo -e "${YELLOW}Log file:${NC} $LOG_FILE"
    echo ""
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    echo -e "${GREEN}============================================================================${NC}"
    echo -e "${GREEN}SNOMED CT Indian Drug Database Setup${NC}"
    echo -e "${GREEN}============================================================================${NC}"
    echo ""
    
    create_logs_dir
    log "Starting SNOMED setup..."
    
    check_prerequisites
    setup_database_schema
    load_data
    verify_data
    create_indexes
    
    print_summary
    
    log "Setup completed successfully!"
}

# Run main function
main "$@"
