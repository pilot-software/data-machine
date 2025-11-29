# 🚀 HMS Terminology API v1 - Consolidated Endpoints

**Base URL**: `http://localhost:8001`

## 📊 Summary

**Total Endpoints**: 11 (reduced from 20+)
- Health: 2
- ICD-10/11: 3
- Drugs: 3
- AB-HBP: 2
- Root: 1

---

## 🏥 Health Endpoints

### 1. Basic Health Check
```bash
GET /api/v1/health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "HMS Terminology Service"
}
```

### 2. Detailed Health Check
```bash
GET /api/v1/health/detailed
```

**Response**:
```json
{
  "status": "healthy",
  "database": "healthy",
  "redis": "not_configured"
}
```

---

## 🔍 ICD-10/11 Endpoints

### 3. Unified ICD Search
**Replaces**: `/search/unified`, `/search/icd10`, `/enterprise/search/icd10/advanced`, `/autocomplete/icd10`

```bash
GET /api/v1/icd10/search
```

**Parameters**:
- `q` (required): Search query (min 2 chars)
- `systems` (optional): Comma-separated systems (default: "icd10,icd11")
- `chapter` (optional): Filter by chapter (e.g., "E")
- `fuzzy` (optional): Fuzzy threshold 0.1-1.0 (default: 0.3)
- `autocomplete` (optional): Autocomplete mode (default: false)
- `limit` (optional): Max results 1-50 (default: 10)

**Examples**:
```bash
# Basic search
curl "http://localhost:8001/api/v1/icd10/search?q=diabetes"

# Search only ICD-10
curl "http://localhost:8001/api/v1/icd10/search?q=fever&systems=icd10"

# Filter by chapter
curl "http://localhost:8001/api/v1/icd10/search?q=diabetes&chapter=E"

# Autocomplete mode
curl "http://localhost:8001/api/v1/icd10/search?q=dia&autocomplete=true&limit=5"

# Fuzzy search
curl "http://localhost:8001/api/v1/icd10/search?q=diabetis&fuzzy=0.5"
```

**Response**:
```json
{
  "query": "diabetes",
  "systems": ["icd10", "icd11"],
  "autocomplete_mode": false,
  "results": {
    "icd10": [
      {
        "code": "E11",
        "term": "Type 2 diabetes mellitus",
        "short_desc": "Type 2 diabetes",
        "chapter": "Endocrine",
        "relevance": 2
      }
    ],
    "icd11": []
  },
  "total": 1,
  "response_time_ms": 45.2
}
```

### 4. Get ICD Code Details
**Replaces**: `/code/{code}`, `/enterprise/icd10/{code}/hierarchy`

```bash
GET /api/v1/icd10/{code}
```

**Parameters**:
- `hierarchy` (optional): Include parent/children (default: false)

**Examples**:
```bash
# Basic lookup
curl "http://localhost:8001/api/v1/icd10/E11"

# With hierarchy
curl "http://localhost:8001/api/v1/icd10/E11?hierarchy=true"
```

**Response**:
```json
{
  "code": "E11",
  "term": "Type 2 diabetes mellitus",
  "short_desc": "Type 2 diabetes",
  "chapter": "Endocrine",
  "parent": {
    "code": "E10-E14",
    "term": "Diabetes mellitus"
  },
  "children": [
    {"code": "E11.0", "term": "Type 2 diabetes with hyperosmolarity"},
    {"code": "E11.1", "term": "Type 2 diabetes with ketoacidosis"}
  ]
}
```

### 5. Get ICD-10 Chapters
```bash
GET /api/v1/icd10/chapters
```

**Response**:
```json
{
  "chapters": [
    {"code": "A-B", "name": "Infectious and parasitic diseases"},
    {"code": "C-D", "name": "Neoplasms"},
    {"code": "E", "name": "Endocrine, nutritional and metabolic"}
  ]
}
```

---

## 💊 Drug Endpoints

### 6. Unified Drug Search
```bash
GET /api/v1/drugs/search
```

**Parameters**:
- `q` (required): Search query (min 2 chars)

**Search Types**:
- Brand name: "Crocin", "Dolo 650"
- Generic name: "Paracetamol", "Metformin"
- Symptom: "fever", "diabetes", "headache"

**Examples**:
```bash
# Search by brand
curl "http://localhost:8001/api/v1/drugs/search?q=crocin"

# Search by generic
curl "http://localhost:8001/api/v1/drugs/search?q=metformin"

# Search by symptom
curl "http://localhost:8001/api/v1/drugs/search?q=fever"
```

**Response**:
```json
{
  "query": "metformin",
  "found": true,
  "total": 15,
  "drugs": [
    {
      "brand_id": 1,
      "brand_name": "Glycomet 500",
      "manufacturer": "USV Ltd",
      "generic_name": "Metformin",
      "rxnorm_cui": "6809",
      "atc_code": "A10BA02",
      "strength": "500mg",
      "dosage_form": "Tablet",
      "mrp": 25.50,
      "pack_size": "10 tablets",
      "indications": "Type 2 diabetes mellitus",
      "symptoms": "High blood sugar",
      "relevance": 2
    }
  ],
  "response_time_ms": 32.1
}
```

### 7. Get Drug Details
```bash
GET /api/v1/drugs/{drug_id}
```

**Example**:
```bash
curl "http://localhost:8001/api/v1/drugs/1"
```

### 8. Check Drug Interactions
```bash
POST /api/v1/drugs/interactions
```

**Request Body**:
```json
{
  "drug_ids": [1, 2, 3]
}
```

**Response**:
```json
{
  "drug_ids": [1, 2, 3],
  "has_interactions": true,
  "count": 1,
  "interactions": [
    {
      "severity": "moderate",
      "description": "May increase risk of hypoglycemia",
      "clinical_effect": "Monitor blood sugar levels",
      "drug_a": "Metformin",
      "drug_b": "Glimepiride"
    }
  ]
}
```

---

## 🏥 Ayushman Bharat HBP Endpoints

### 9. Search AB-HBP Procedures
```bash
GET /api/v1/abhbp/search
```

**Parameters**:
- `q` (required): Search query (min 2 chars)
- `specialty` (optional): Filter by specialty
- `limit` (optional): Max results (default: 20, max: 100)

**Examples**:
```bash
# Basic search
curl "http://localhost:8001/api/v1/abhbp/search?q=surgery"

# Filter by specialty
curl "http://localhost:8001/api/v1/abhbp/search?q=surgery&specialty=cardiology"
```

**Response**:
```json
{
  "query": "surgery",
  "count": 5,
  "results": [
    {
      "package_code": "PKG001",
      "package_name": "Coronary Artery Bypass Grafting",
      "specialty": "Cardiology",
      "base_rate": 150000.00,
      "procedure_type": "Surgical"
    }
  ]
}
```

### 10. Get AB-HBP Procedure Details
```bash
GET /api/v1/abhbp/{package_code}
```

**Example**:
```bash
curl "http://localhost:8001/api/v1/abhbp/PKG001"
```

**Response**:
```json
{
  "package_code": "PKG001",
  "package_name": "Coronary Artery Bypass Grafting",
  "specialty": "Cardiology",
  "procedure_type": "Surgical",
  "base_rate": 150000.00,
  "icd10_codes": ["I25.1", "I25.2"],
  "preauth_required": true
}
```

---

## 🎯 Quick Test

```bash
# Make script executable
chmod +x test_api.sh

# Run tests
./test_api.sh
```

---

## 📊 Performance

- **Response Time**: < 50ms (avg)
- **Concurrent Requests**: 100+ req/sec
- **Database**: PostgreSQL with indexes
- **Caching**: Redis (optional)

---

## 🔒 Security

- Input validation (Pydantic)
- SQL injection prevention (parameterized queries)
- Rate limiting (middleware)
- CORS configured

---

## 📚 Interactive Documentation

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

---

## 🆚 Migration from Old Endpoints

| Old Endpoint | New Endpoint |
|-------------|--------------|
| `/api/v1/search/unified` | `/api/v1/icd10/search?systems=icd10,icd11` |
| `/api/v1/search/icd10` | `/api/v1/icd10/search?systems=icd10` |
| `/api/v1/autocomplete/icd10` | `/api/v1/icd10/search?autocomplete=true` |
| `/api/v1/enterprise/search/icd10/advanced` | `/api/v1/icd10/search?fuzzy=0.5` |
| `/api/v1/code/{code}` | `/api/v1/icd10/{code}` |
| `/api/v1/enterprise/icd10/{code}/hierarchy` | `/api/v1/icd10/{code}?hierarchy=true` |
| `/api/v1/drugs/quick/{id}` | `/api/v1/drugs/{id}` |
| `/api/v1/drugs/check-interaction` | `/api/v1/drugs/interactions` |

---

**Built for Indian Healthcare** 🇮🇳
