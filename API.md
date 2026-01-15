# 📚 API Documentation - Essential Endpoints

## 🔑 Authentication

All endpoints require API key in header:
```bash
X-API-Key: dev-key-123
```

---

## 🏆 Top 5 Most Useful Endpoints

### 1. AI Diagnosis (Natural Language) ⭐⭐⭐⭐⭐

**Endpoint**: `POST /api/v1/clinical-ai/diagnose-text`

**Use Case**: Doctor types symptoms naturally, AI provides diagnosis

**Request**:
```bash
curl -X POST "http://localhost:8001/api/v1/clinical-ai/diagnose-text?prompt=patient%20has%20fever%20and%20cough%20for%203%20days" \
  -H "X-API-Key: dev-key-123"
```

**Response**:
```json
{
  "diagnosis_suggestions": [{
    "condition": "Viral Fever",
    "icd10_code": "J069",
    "icd10_description": "Acute upper respiratory infection",
    "confidence": "high",
    "reasoning": "Fever and cough indicate respiratory infection"
  }],
  "recommended_drugs": [{
    "snomed_id": 123456,
    "brand_name": "Crocin 500mg",
    "generic_name": "Paracetamol 500mg"
  }],
  "red_flags": ["High fever >103F", "Difficulty breathing"]
}
```

---

### 2. Drug Search ⭐⭐⭐⭐⭐

**Endpoint**: `GET /api/v1/snomed/search`

**Use Case**: Find any drug from 89K brands

**Request**:
```bash
curl "http://localhost:8001/api/v1/snomed/search?q=paracetamol&page=1&page_size=20" \
  -H "X-API-Key: dev-key-123"
```

**Response**:
```json
{
  "total": 4426,
  "page": 1,
  "results": [{
    "snomed_id": 2430421000189104,
    "brand_name": "Crocin 500mg oral tablet",
    "generic_name": "Paracetamol 500mg",
    "supplier_name": "GlaxoSmithKline"
  }]
}
```

---

### 3. Get Drug Alternatives ⭐⭐⭐⭐

**Endpoint**: `GET /api/v1/snomed/brands/{id}/alternatives`

**Use Case**: Find cheaper/available alternatives (same generic)

**Request**:
```bash
curl "http://localhost:8001/api/v1/snomed/brands/2430421000189104/alternatives" \
  -H "X-API-Key: dev-key-123"
```

**Response**:
```json
{
  "original_brand": {
    "snomed_id": 2430421000189104,
    "brand_name": "Crocin 500mg",
    "generic_name": "Paracetamol 500mg"
  },
  "alternatives": [{
    "snomed_id": 2430422000189105,
    "brand_name": "Dolo 650mg",
    "generic_name": "Paracetamol 650mg",
    "supplier_name": "Micro Labs"
  }]
}
```

---

### 4. ICD Code Search ⭐⭐⭐⭐

**Endpoint**: `GET /api/v1/icd/search`

**Use Case**: Get ICD-10 codes for insurance claims

**Request**:
```bash
curl "http://localhost:8001/api/v1/icd/search?q=diabetes" \
  -H "X-API-Key: dev-key-123"
```

**Response**:
```json
{
  "total": 20,
  "results": [{
    "code": "E11",
    "term": "Type 2 diabetes mellitus",
    "category": "Endocrine diseases"
  }, {
    "code": "E10",
    "term": "Type 1 diabetes mellitus",
    "category": "Endocrine diseases"
  }]
}
```

---

### 5. Get All Antibiotics ⭐⭐⭐

**Endpoint**: `GET /api/v1/snomed/extended/antibiotics`

**Use Case**: Quick access to all 34K antibiotics

**Request**:
```bash
curl "http://localhost:8001/api/v1/snomed/extended/antibiotics?page=1&page_size=20" \
  -H "X-API-Key: dev-key-123"
```

**Response**:
```json
{
  "total": 34042,
  "page": 1,
  "antibiotics": [{
    "snomed_id": 123456,
    "brand_name": "Amoxil 500mg",
    "generic_name": "Amoxicillin 500mg",
    "drug_class": "Antibiotic"
  }]
}
```

---

## 🔄 Typical Workflow

```javascript
// 1. Patient describes symptoms
const symptoms = "fever, cough, body ache for 3 days";

// 2. AI Diagnosis
const diagnosis = await fetch('/api/v1/clinical-ai/diagnose-text', {
  method: 'POST',
  headers: { 'X-API-Key': 'dev-key-123' },
  body: JSON.stringify({ prompt: symptoms })
});

// 3. Search recommended drug
const drugName = diagnosis.recommended_drugs[0].generic_name;
const drugs = await fetch(`/api/v1/snomed/search?q=${drugName}`, {
  headers: { 'X-API-Key': 'dev-key-123' }
});

// 4. Get alternatives (if needed)
const alternatives = await fetch(
  `/api/v1/snomed/brands/${drugs.results[0].snomed_id}/alternatives`,
  { headers: { 'X-API-Key': 'dev-key-123' } }
);

// 5. Get ICD code for insurance
const icd = await fetch(`/api/v1/icd/search?q=${diagnosis.condition}`, {
  headers: { 'X-API-Key': 'dev-key-123' }
});
```

---

## 📊 Additional Useful Endpoints

### Drug Classifications
```bash
# Get all drug classes
GET /api/v1/snomed/extended/drug-classes

# Get drugs by class
GET /api/v1/snomed/extended/by-class/analgesic
```

### Drug Details
```bash
# Get brand details
GET /api/v1/snomed/brands/{id}

# Get generic details
GET /api/v1/snomed/generics/{id}
```

### Health Check
```bash
# Check API status
GET /api/v1/health
```

---

## 🚀 Interactive Documentation

Visit: **http://localhost:8001/docs**

Try all endpoints with Swagger UI!

---

## 💡 Best Practices

1. **Always validate ICD codes** from AI response against database
2. **Show drug alternatives** to give patients options
3. **Cache frequent searches** (paracetamol, antibiotics)
4. **Use natural language** for better user experience
5. **Include red flags** in UI to alert doctors

---

## 📈 Performance

- Drug Search: < 50ms
- AI Diagnosis: < 2s (Groq)
- ICD Search: < 30ms
- Get Alternatives: < 100ms

---

## 🔐 Security

- API Key required for all endpoints
- Rate limiting: 100 req/min per IP
- Input sanitization enabled
- Audit logging active
