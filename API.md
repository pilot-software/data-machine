# 📚 API Documentation - Essential Endpoints

## 🔑 Authentication

All endpoints require API key in header:
```bash
X-API-Key: dev-key-123
```

---

## 🏆 Top 5 Most Useful Endpoints

### 1. AI Diagnosis (Natural Language) ⭐⭐⭐⭐⭐ 🤖 AI + 💾 DB

**Endpoint**: `POST /api/v1/clinical-ai/diagnose-text`

**Use Case**: Doctor types symptoms naturally, AI provides diagnosis

**How it works**: 
- 🤖 **Groq AI**: Analyzes symptoms, suggests diagnosis
- 💾 **Database**: Validates ICD-10 codes, finds SNOMED drugs

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

### 2. Drug Search ⭐⭐⭐⭐⭐ 💾 DB Only

**Endpoint**: `GET /api/v1/snomed/search`

**Use Case**: Find any drug from 89K brands

**How it works**: 
- 💾 **Database**: Fast search across 89,446 SNOMED brands

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

### 3. Get Drug Alternatives ⭐⭐⭐⭐ 💾 DB Only

**Endpoint**: `GET /api/v1/snomed/brands/{id}/alternatives`

**Use Case**: Find cheaper/available alternatives (same generic)

**How it works**: 
- 💾 **Database**: Finds all brands with same generic formulation

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

### 4. ICD Code Search ⭐⭐⭐⭐ 💾 DB Only

**Endpoint**: `GET /api/v1/icd/search`

**Use Case**: Get ICD-10 codes for insurance claims

**How it works**: 
- 💾 **Database**: Searches 71,704 ICD-10 codes

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

### 5. Get All Antibiotics ⭐⭐⭐ 💾 DB Only

**Endpoint**: `GET /api/v1/snomed/extended/antibiotics`

**Use Case**: Quick access to all 34K antibiotics

**How it works**: 
- 💾 **Database**: Returns pre-classified antibiotics from 34,042 drugs

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

// 2. AI Diagnosis (🤖 AI + 💾 DB)
const diagnosis = await fetch('/api/v1/clinical-ai/diagnose-text', {
  method: 'POST',
  headers: { 'X-API-Key': 'dev-key-123' },
  body: JSON.stringify({ prompt: symptoms })
});
// Groq analyzes → Database validates ICD & finds drugs

// 3. Search recommended drug (💾 DB Only)
const drugName = diagnosis.recommended_drugs[0].generic_name;
const drugs = await fetch(`/api/v1/snomed/search?q=${drugName}`, {
  headers: { 'X-API-Key': 'dev-key-123' }
});
// Database searches 89K brands

// 4. Get alternatives (💾 DB Only)
const alternatives = await fetch(
  `/api/v1/snomed/brands/${drugs.results[0].snomed_id}/alternatives`,
  { headers: { 'X-API-Key': 'dev-key-123' } }
);
// Database finds same generic

// 5. Get ICD code for insurance (💾 DB Only)
const icd = await fetch(`/api/v1/icd/search?q=${diagnosis.condition}`, {
  headers: { 'X-API-Key': 'dev-key-123' }
});
// Database searches ICD codes
```

---

## 📊 Additional Useful Endpoints

### Drug Classifications (💾 DB Only)
```bash
# Get all drug classes
GET /api/v1/snomed/extended/drug-classes

# Get drugs by class
GET /api/v1/snomed/extended/by-class/analgesic
```

### Drug Details (💾 DB Only)
```bash
# Get brand details
GET /api/v1/snomed/brands/{id}

# Get generic details
GET /api/v1/snomed/generics/{id}
```

### Health Check (💾 DB Only)
```bash
# Check API status
GET /api/v1/health
```

---

## 🎯 AI vs Database Endpoints

### 🤖 AI-Powered (Groq + Database)
- `POST /api/v1/clinical-ai/diagnose` - Structured diagnosis
- `POST /api/v1/clinical-ai/diagnose-text` - Natural language diagnosis

### 💾 Database Only (Fast, No AI)
- `GET /api/v1/snomed/search` - Drug search
- `GET /api/v1/snomed/brands/{id}/alternatives` - Drug alternatives
- `GET /api/v1/icd/search` - ICD code search
- `GET /api/v1/snomed/extended/antibiotics` - Get antibiotics
- `GET /api/v1/snomed/extended/by-class/{class}` - Get by drug class
- All other endpoints

**Note**: AI endpoints use Groq for intelligence, then validate against database for accuracy!

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
