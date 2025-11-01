# 🏥 HMS Terminology Service - Indian Drug Database

Enterprise-grade FastAPI microservice for medical terminology (ICD-10, ICD-11) with **Indian Drug Database**, RxNorm mapping, and auto-updates.

## 🚀 Quick Start

```bash
# Setup database
psql -d hms_terminology -f scripts/setup_drug_db.sql

# Load sample data
python scripts/etl/load_sample_data.py

# Start service
python -m uvicorn app.main:app --reload
```

**API**: `http://localhost:8001/docs`

## 📊 Database Coverage

- **ICD-10**: 71,704 codes
- **ICD-11**: 4,239 codes  
- **Indian Drugs**: 114+ brands, 60+ generics
- **RxNorm Mapping**: Complete

## 🔍 API Endpoints

### Drug Search (Unified)
```bash
# Search by brand, generic, or symptom
GET /api/v1/drugs/search?q=metformin
GET /api/v1/drugs/search?q=crocin
GET /api/v1/drugs/search?q=fever
```

### ICD Codes
```bash
GET /api/v1/search/unified?query=diabetes
GET /api/v1/icd10/{code}
```

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
# Download 405+ drugs from OpenFDA (FREE)
python scripts/etl/download_opensource_data.py

# Download 100+ Indian drugs
python scripts/etl/download_expanded_data.py
```

## 🎯 Features

✅ Indian Brand ↔ RxNorm ↔ Generic mapping  
✅ Symptom-based drug search  
✅ Multi-language support (ready)  
✅ Auto-updates via cron  
✅ 100% open-source data sources  

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
