# 🚀 HMS Terminology API - Quick Reference

## Base URL
```
http://localhost:8001
```

---

## 🏥 Health
```bash
GET /api/v1/health                    # Basic health
GET /api/v1/health/detailed           # Detailed health
```

---

## 🔍 ICD-10/11 Search

### Search (All-in-One)
```bash
GET /api/v1/icd10/search?q={query}&systems={icd10,icd11}&chapter={E}&fuzzy={0.3}&autocomplete={false}&limit={10}
```

**Examples**:
```bash
# Basic
curl "localhost:8001/api/v1/icd10/search?q=diabetes"

# ICD-10 only
curl "localhost:8001/api/v1/icd10/search?q=fever&systems=icd10"

# With chapter filter
curl "localhost:8001/api/v1/icd10/search?q=diabetes&chapter=E"

# Autocomplete
curl "localhost:8001/api/v1/icd10/search?q=dia&autocomplete=true&limit=5"

# Fuzzy search
curl "localhost:8001/api/v1/icd10/search?q=diabetis&fuzzy=0.5"
```

### Code Details
```bash
GET /api/v1/icd10/{code}?hierarchy={false}
```

**Examples**:
```bash
# Basic
curl "localhost:8001/api/v1/icd10/E11"

# With hierarchy
curl "localhost:8001/api/v1/icd10/E11?hierarchy=true"
```

### Chapters
```bash
GET /api/v1/icd10/chapters
```

---

## 💊 Drugs

### Search
```bash
GET /api/v1/drugs/search?q={query}
```

**Examples**:
```bash
# By brand
curl "localhost:8001/api/v1/drugs/search?q=crocin"

# By generic
curl "localhost:8001/api/v1/drugs/search?q=metformin"

# By symptom
curl "localhost:8001/api/v1/drugs/search?q=fever"
```

### Details
```bash
GET /api/v1/drugs/{id}
```

### Interactions
```bash
POST /api/v1/drugs/interactions
Content-Type: application/json

{"drug_ids": [1, 2, 3]}
```

---

## 🏥 Ayushman Bharat HBP

### Search
```bash
GET /api/v1/abhbp/search?q={query}&specialty={cardiology}&limit={20}
```

**Example**:
```bash
curl "localhost:8001/api/v1/abhbp/search?q=surgery&specialty=cardiology"
```

### Details
```bash
GET /api/v1/abhbp/{package_code}
```

---

## 🧪 Quick Test

```bash
# Make executable
chmod +x test_api.sh

# Run tests
./test_api.sh
```

---

## 📚 Full Docs

- **Swagger**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **Full Guide**: `docs/API_ENDPOINTS_V1.md`

---

## 🎯 Common Use Cases

### 1. Search for a disease
```bash
curl "localhost:8001/api/v1/icd10/search?q=diabetes&limit=5"
```

### 2. Get code with related codes
```bash
curl "localhost:8001/api/v1/icd10/E11?hierarchy=true"
```

### 3. Find drug by symptom
```bash
curl "localhost:8001/api/v1/drugs/search?q=headache"
```

### 4. Check drug interactions
```bash
curl -X POST "localhost:8001/api/v1/drugs/interactions" \
  -H "Content-Type: application/json" \
  -d '{"drug_ids": [1, 2]}'
```

### 5. Search AB-HBP procedures
```bash
curl "localhost:8001/api/v1/abhbp/search?q=bypass"
```

---

## 📊 Response Format

All endpoints return JSON:
```json
{
  "query": "diabetes",
  "total": 10,
  "results": [...],
  "response_time_ms": 45.2
}
```

---

## ⚡ Performance

- Response time: < 50ms
- Rate limit: 100 req/min
- Max results: 50 per request

---

**Built for Indian Healthcare** 🇮🇳
