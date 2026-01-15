#!/bin/bash
# Complete HMS Terminology Service Setup & Start
# Run this on a fresh machine to get everything working

set -e

echo "=========================================="
echo "HMS Terminology Service - Complete Setup"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${RED}❌ Don't run as root${NC}"
   exit 1
fi

# 1. Check Prerequisites
echo "Step 1: Checking prerequisites..."
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}❌ Python3 required${NC}"; exit 1; }
command -v psql >/dev/null 2>&1 || { echo -e "${RED}❌ PostgreSQL required${NC}"; exit 1; }
echo -e "${GREEN}✓ Prerequisites OK${NC}"
echo ""

# 2. Install Python Dependencies
echo "Step 2: Installing Python dependencies..."
pip3 install -r requirements.txt --quiet
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# 3. Setup Environment
echo "Step 3: Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠ Edit .env file with your database credentials${NC}"
    read -p "Press Enter after editing .env..."
fi
source .env
echo -e "${GREEN}✓ Environment configured${NC}"
echo ""

# 4. Create Database
echo "Step 4: Setting up database..."
DB_EXISTS=$(psql -U ${DB_USER:-samirkolhe} -lqt | cut -d \| -f 1 | grep -w ${DB_NAME:-medical_library} | wc -l)
if [ $DB_EXISTS -eq 0 ]; then
    createdb -U ${DB_USER:-samirkolhe} ${DB_NAME:-medical_library}
    echo -e "${GREEN}✓ Database created${NC}"
else
    echo -e "${YELLOW}⚠ Database already exists${NC}"
fi
echo ""

# 5. Create Schema
echo "Step 5: Creating database schema..."
psql -U ${DB_USER:-samirkolhe} -d ${DB_NAME:-medical_library} -f scripts/setup_drug_db.sql > /dev/null 2>&1
psql -U ${DB_USER:-samirkolhe} -d ${DB_NAME:-medical_library} -f scripts/setup_snomed_db.sql > /dev/null 2>&1
echo -e "${GREEN}✓ Schema created${NC}"
echo ""

# 6. Load ICD Data
echo "Step 6: Loading ICD-10/11 codes..."
if [ -f "data/icd10_full_processed.csv" ]; then
    python3 scripts/etl/load_sample_data.py > /dev/null 2>&1
    echo -e "${GREEN}✓ ICD codes loaded${NC}"
else
    echo -e "${YELLOW}⚠ ICD data not found, downloading...${NC}"
    python3 scripts/etl/download_icd10_complete.py
    python3 scripts/etl/load_sample_data.py > /dev/null 2>&1
    echo -e "${GREEN}✓ ICD codes loaded${NC}"
fi
echo ""

# 7. Load SNOMED Drug Data
echo "Step 7: Loading SNOMED CT Indian Drug Database..."
if [ -d "CommonDrugCodesForIndia_FlatFilePackage" ]; then
    python3 scripts/etl/load_snomed_data.py
    echo -e "${GREEN}✓ SNOMED drugs loaded (89K+ brands)${NC}"
else
    echo -e "${RED}❌ CommonDrugCodesForIndia_FlatFilePackage not found${NC}"
    echo "Download from: https://www.nrces.in/standards/snomed-ct"
    exit 1
fi
echo ""

# 8. Load RF2 Extended Data (Optional)
echo "Step 8: Loading RF2 extended data (hierarchies, classifications)..."
if [ -d "SnomedCT_IndiaDrugExtensionRF2_PRODUCTION_IN1000189_20251219T120000Z" ]; then
    python3 scripts/etl/load_snomed_rf2_extended.py
    
    # Classify drugs
    psql -U ${DB_USER:-samirkolhe} -d ${DB_NAME:-medical_library} << 'EOF' > /dev/null 2>&1
UPDATE snomed_drug_classes c SET is_antibiotic = TRUE, drug_class = 'Antibiotic'
FROM snomed_brands b JOIN snomed_generics g ON b.generic_id = g.snomed_id
WHERE c.drug_id = b.snomed_id AND (g.generic_name ~* 'cillin|mycin|floxacin|cycline|azole|sulfa|cef|mero|vanco|strepto');

UPDATE snomed_drug_classes c SET is_analgesic = TRUE, drug_class = 'Analgesic'
FROM snomed_brands b JOIN snomed_generics g ON b.generic_id = g.snomed_id
WHERE c.drug_id = b.snomed_id AND (g.generic_name ~* 'paracetamol|ibuprofen|aspirin|morphine|tramadol|codeine|fentanyl');

UPDATE snomed_drug_classes c SET is_antihypertensive = TRUE, drug_class = 'Antihypertensive'
FROM snomed_brands b JOIN snomed_generics g ON b.generic_id = g.snomed_id
WHERE c.drug_id = b.snomed_id AND (g.generic_name ~* 'amlodipine|enalapril|losartan|metoprolol|atenolol|lisinopril');

UPDATE snomed_drug_classes c SET is_antidiabetic = TRUE, drug_class = 'Antidiabetic'
FROM snomed_brands b JOIN snomed_generics g ON b.generic_id = g.snomed_id
WHERE c.drug_id = b.snomed_id AND (g.generic_name ~* 'metformin|glipizide|insulin|sitagliptin|pioglitazone');

UPDATE snomed_drug_classes c SET is_antiinflammatory = TRUE, drug_class = 'Anti-inflammatory'
FROM snomed_brands b JOIN snomed_generics g ON b.generic_id = g.snomed_id
WHERE c.drug_id = b.snomed_id AND (g.generic_name ~* 'ibuprofen|diclofenac|naproxen|indomethacin|prednisolone');
EOF
    echo -e "${GREEN}✓ RF2 extended data loaded${NC}"
else
    echo -e "${YELLOW}⚠ RF2 folder not found, skipping extended features${NC}"
fi
echo ""

# 9. Create logs directory
mkdir -p logs

# 10. Start Server
echo "Step 9: Starting server..."
pkill -f "uvicorn app.main:app" 2>/dev/null || true
sleep 2
nohup uvicorn app.main:app --host 0.0.0.0 --port 8001 > logs/server.log 2>&1 &
sleep 3

# 11. Test Server
echo "Step 10: Testing server..."
if curl -s http://localhost:8001/api/v1/health > /dev/null; then
    echo -e "${GREEN}✓ Server running${NC}"
else
    echo -e "${RED}❌ Server failed to start. Check logs/server.log${NC}"
    exit 1
fi
echo ""

# 12. Summary
echo "=========================================="
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "📊 Database Statistics:"
psql -U ${DB_USER:-samirkolhe} -d ${DB_NAME:-medical_library} -t << 'EOF'
SELECT 
  'ICD-10 Codes: ' || COUNT(*) FROM icd10_codes
UNION ALL
SELECT 
  'SNOMED Brands: ' || COUNT(*) FROM snomed_brands
UNION ALL
SELECT 
  'SNOMED Generics: ' || COUNT(*) FROM snomed_generics
UNION ALL
SELECT 
  'Antibiotics: ' || COUNT(*) FROM snomed_drug_classes WHERE is_antibiotic;
EOF
echo ""
echo "🌐 API Endpoints:"
echo "  Health:      http://localhost:8001/api/v1/health"
echo "  API Docs:    http://localhost:8001/docs"
echo "  ICD Search:  http://localhost:8001/api/v1/icd/search?q=diabetes"
echo "  Drug Search: http://localhost:8001/api/v1/snomed/search?q=paracetamol"
echo "  AI Diagnose: http://localhost:8001/api/v1/clinical-ai/diagnose"
echo ""
echo "🔑 API Key: dev-key-123"
echo ""
echo "📝 Logs: tail -f logs/server.log"
echo ""
echo "🛑 Stop: pkill -f 'uvicorn app.main:app'"
echo ""
