# 🏥 HMS Terminology Service - Indian Drug Database

Enterprise-grade FastAPI microservice for medical terminology (ICD-10, ICD-11) with **Indian Drug Database**, RxNorm mapping, and auto-updates.

## 🚀 Quick Start (New Developers)

```bash
# 1. Clone repository
git clone <repository-url>
cd data-machine

# 2. Run setup (installs everything)
./setup.sh

# 3. Start service
./start.sh

# 4. Test API
./test_api.sh
```

**API Docs**: `http://localhost:8001/docs`
**Setup Guide**: See `SETUP_GUIDE.md` for detailed instructions

## 📊 Database Coverage

- **ICD-10**: 171,704 codes (complete with subcodes)
- **ICD-11**: 4,239 codes  
- **Indian Drugs**: 114+ brands, 60+ generics
- **RxNorm Mapping**: Complete

## 🔍 API Endpoints

### 🔐 Authentication Required

All API endpoints require an API key in the header:

```bash
X-API-Key: dev-key-123
```

**Available API Keys** (from .env):
- `dev-key-123` - Development
- `prod-key-xyz` - Production
- `frontend-key-abc` - Frontend

### ICD-10/11 Search
```bash
# Unified search
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/icd/search?q=diabetes"

# With autocomplete
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/icd/search?q=dia&autocomplete=true"

# Get code details
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/icd/E11?hierarchy=true"
```

### Drug Search
```bash
# Search by brand, generic, or symptom
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/drugs/search?q=metformin"

curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/drugs/search?q=fever"
```

### Health Check (No Auth)
```bash
# Public endpoint
curl http://localhost:8001/api/v1/health
```

**Total Endpoints**: 11 organized by domain
**See**: `API_QUICK_REFERENCE.md` for complete list

## 📁 Project Structure

```
├── app/                    # FastAPI application
│   ├── api/               # API endpoints
│   ├── db/                # Database models
│   └── services/          # Business logic
├── scripts/               # Utility scripts
│   ├── etl/              # Data loading scripts
│   ├── cron/             # Auto-update scripts
│   └── setup_drug_db.sql # Database schema
├── docs/                  # Documentation
└── data/                  # Data files (gitignored)
```

## 🔄 Auto-Update Setup

```bash
# Setup weekly auto-updates
./scripts/cron/setup_cron.sh

# Manual update
./scripts/cron/cron_update_drugs.sh
```

## 📖 Documentation

- [Drug ETL Guide](docs/README_DRUG_ETL.md)
- [Data Sources](docs/DATA_SOURCES.md)
- [API Endpoints](docs/FINAL_API_ENDPOINTS.md)
- [Cron Setup](docs/CRON_SETUP.md)
- [Open Source Data](docs/OPENSOURCE_DATA_SOURCES.md)

## 🆓 Get More Data

```bash
# Download complete ICD-10-CM codes (100K+ codes)
python scripts/etl/download_icd10_complete.py

# Download 405+ drugs from OpenFDA (FREE)
python scripts/etl/download_opensource_data.py

# Download 100+ Indian drugs
python scripts/etl/download_expanded_data.py
```

## 🎯 Features

✅ Indian Brand ↔ RxNorm ↔ Generic mapping  
✅ Symptom-based drug search  
✅ API Key authentication  
✅ Auto-updates via cron  
✅ 100% open-source data sources  
✅ Domain-organized endpoints  

## 📊 Data Sources

- **OpenFDA**: 100,000+ drugs (FREE)
- **RxNorm**: 2M+ concepts (FREE)
- **NPPA**: Indian drug prices (FREE)
- **DrugBank**: 14,000+ drugs (FREE)

See [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) for details.

## 🔧 Requirements

```bash
pip install -r requirements.txt
```

## 🚀 Production Ready

- ✅ Fast API (<50ms response)
- ✅ PostgreSQL with indexes
- ✅ Redis caching
- ✅ Rate limiting
- ✅ Error handling
- ✅ Structured logging

---

**Built for Indian Healthcare Market** 🇮🇳
