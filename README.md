# 🏥 HMS Terminology Service - Indian Drug Database

Enterprise-grade FastAPI microservice for medical terminology (ICD-10, ICD-11) with **Indian Drug Database**, **SNOMED CT** (89K+ brands), and **AI Clinical Assistant**.

## 🚀 Quick Start (2 Minutes)

```bash
git clone <repository-url>
cd data-machine
./import_database.sh database_dumps/hms_database_20260115_112015.tar.gz
./start.sh
```

**API Docs**: http://localhost:8001/docs  
**API Key**: `dev-key-123`

## 📊 What's Inside

- **89,446** Indian drug brands (SNOMED CT)
- **71,704** ICD-10 diagnosis codes
- **34,042** Antibiotics classified
- **9,869** Generic formulations
- **7,934** Manufacturers
- **AI Diagnosis** with Grok/Ollama

## 🔍 Key Features

### 1. Drug Search
```bash
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/search?q=paracetamol"
```

### 2. AI Diagnosis
```bash
curl -X POST -H "X-API-Key: dev-key-123" \
  -H "Content-Type: application/json" \
  -d '{"symptoms":["fever","cough"],"patient_age":35}' \
  "http://localhost:8001/api/v1/clinical-ai/diagnose"
```

### 3. Get All Antibiotics
```bash
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/extended/antibiotics"
```

### 4. ICD Code Search
```bash
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/icd/search?q=diabetes"
```

## 📖 Documentation

- **[Deployment Guide](DEPLOYMENT.md)** - Production setup
- **[Workflow Guide](WORKFLOW.md)** - Usage patterns
- **[LLM Setup](LLM_SETUP_GUIDE.md)** - AI configuration
- **[API Docs](http://localhost:8001/docs)** - Interactive API explorer

## 🛠️ Daily Commands

```bash
./start.sh    # Start server
./stop.sh     # Stop server
./status.sh   # Check status
./test_all.sh # Run tests
```

## 🔄 Update Data

```bash
# Export new database dump
./export_database.sh

# Import updated dump
./import_database.sh database_dumps/hms_database_new.tar.gz
```

## 🎯 Use Cases

- **Hospitals**: Electronic prescriptions with SNOMED codes
- **Insurance**: ICD-10 coding for claims
- **Pharmacies**: Drug search and alternatives
- **Doctors**: AI-powered diagnosis assistance
- **Research**: Drug classification and analysis

---

**Built for Indian Healthcare** 🇮🇳 | **Production Ready** ✅
