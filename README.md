# 🏥 HMS Terminology Service - Indian Drug Database

Enterprise-grade FastAPI microservice for medical terminology (ICD-10, ICD-11) with **Indian Drug Database**, **SNOMED CT** (89K+ brands), RxNorm mapping, and auto-updates.

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

- **SNOMED CT**: 89,446 Indian brands with SNOMED codes 🆕
- **ICD-10**: 171,704 codes (complete with subcodes)
- **ICD-11**: 4,239 codes  
- **Generics**: 9,869 formulations
- **Manufacturers**: 7,934 suppliers
- **Substances**: 28,912 active ingredients

## 🔍 API Endpoints

### 🔐 Authentication

All endpoints require API key:
```bash
X-API-Key: dev-key-123
```

### 🆕 SNOMED CT Drugs (Recommended - 89K+ brands)

```bash
# Search drugs
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/search?q=metformin&page=1&page_size=20"

# Get brand details
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/brands/2430421000189104"

# Find alternatives (same generic)
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/brands/2430421000189104/alternatives"

# Get generic details
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/generics/1321000189104"

# Get brands by generic
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/generics/1321000189104/brands"

# Get supplier details
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/suppliers/1058411000189103"

# Autocomplete
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/autocomplete?q=met&limit=10"

# Statistics
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/stats"
```

### 🤖 AI Clinical Assistant (Natural Language)

```bash
# Natural language diagnosis - just describe symptoms!
curl -X POST -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/clinical-ai/diagnose-text?prompt=frequent%20urination%20burning%20while%20passing%20urine%20lower%20abdominal%20pain%20female%2032%20years"

# Structured diagnosis
curl -X POST -H "X-API-Key: dev-key-123" \
  -H "Content-Type: application/json" \
  -d '{"symptoms": ["cough", "fever"], "patient_age": 35}' \
  "http://localhost:8001/api/v1/clinical-ai/diagnose"

# Check LLM status
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/clinical-ai/status"
```

### 🏥 ICD Codes

```bash
# Search ICD-10/11
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/icd/search?q=diabetes"

# Get code details
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/icd/E11?hierarchy=true"
```

### ❤️ Health Check

```bash
curl http://localhost:8001/api/v1/health
```

**📚 Complete API Documentation**: http://localhost:8001/docs

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

- **[Natural Language API](NATURAL_LANGUAGE_API.md)** - Free-form symptom diagnosis 🆕
- **[LLM Setup Guide](LLM_SETUP_GUIDE.md)** - AWS Bedrock/OpenAI integration 🆕
- **[AI Clinical Assistant](AI_CLINICAL_ASSISTANT.md)** - Amazon Q for doctors
- **[User Guide](USER_GUIDE.md)** - Complete API usage guide
- [SNOMED CT Integration](docs/SNOMED_INTEGRATION.md) - Technical details
- [SNOMED Quick Start](SNOMED_QUICKSTART.md) - 5-minute setup
- [Migration Guide](docs/SNOMED_MIGRATION_GUIDE.md) - Legacy to SNOMED
- [Data Sources](docs/DATA_SOURCES.md) - Data provenance
- [API Endpoints](docs/FINAL_API_ENDPOINTS.md) - Complete reference

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

✅ **AI Clinical Assistant (LLM-Powered)** - Uses AWS Bedrock/OpenAI for intelligent diagnosis 🆕  
✅ **SNOMED CT Integration** - 89K+ Indian brands with global standard codes  
✅ **Natural Language Understanding** - Handles ANY symptom description 🆕  
✅ **Outbreak Detection** - Real-time alerts based on prescription patterns  
✅ **Smart Prescriptions** - Learn from hospital data  
✅ Drug alternatives finder (same generic formulation)  
✅ ICD-10/11 coding for insurance  
✅ API Key authentication  
✅ Fast autocomplete (< 20ms)    

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
