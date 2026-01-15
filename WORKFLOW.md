# 🔄 HMS Terminology Service - Usage Flow

## 📋 Typical Clinical Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    PATIENT VISIT                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  1. SYMPTOM COLLECTION                                       │
│  Doctor enters: "fever, cough, body ache for 3 days"        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2. AI DIAGNOSIS (Grok/Ollama)                              │
│  POST /api/v1/clinical-ai/diagnose-text                     │
│  → Returns: Viral Fever, ICD-10: J06.9                      │
│  → Suggests: paracetamol, cetirizine                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  3. DRUG SEARCH                                              │
│  GET /api/v1/snomed/search?q=paracetamol                    │
│  → Returns: 4,426 brands with SNOMED codes                  │
│  → Doctor selects: Crocin 500mg                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  4. FIND ALTERNATIVES (if needed)                           │
│  GET /api/v1/snomed/brands/{id}/alternatives                │
│  → Returns: Same generic, different brands                  │
│  → Cheaper options, different manufacturers                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  5. PRESCRIPTION GENERATION                                  │
│  - Drug: Crocin 500mg (SNOMED: 123456789)                  │
│  - Diagnosis: Viral Fever (ICD-10: J06.9)                  │
│  - Dosage: 1 tablet TID for 3 days                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  6. INSURANCE CLAIM                                          │
│  - ICD-10 code for billing                                  │
│  - SNOMED code for drug tracking                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏥 Advanced Use Cases

### Use Case 1: Drug Class Search
```
Doctor: "I need an antibiotic for UTI"
↓
GET /api/v1/snomed/extended/antibiotics
↓
Returns: 34,042 antibiotics
↓
Filter by: "fluoroquinolone" or "nitrofurantoin"
↓
Select: Ciprofloxacin 500mg
```

### Use Case 2: Natural Language Diagnosis
```
Patient says: "burning while passing urine, frequent urination"
↓
POST /api/v1/clinical-ai/diagnose-text
  ?prompt=burning while passing urine frequent urination
↓
AI Returns:
  - Diagnosis: Urinary Tract Infection
  - ICD-10: N39.0
  - Drugs: nitrofurantoin, ciprofloxacin
  - Tests: Urine culture, Urinalysis
  - Red Flags: Fever, Blood in urine
```

### Use Case 3: Outbreak Detection
```
Hospital tracks prescriptions
↓
Sudden spike in "Gastroenteritis" diagnoses (ICD: A09)
↓
Alert: Possible food poisoning outbreak
↓
Public health notification
```

---

## 🔄 Integration Flow

### Frontend (React/Angular) → API → Database

```javascript
// 1. Search drugs
const drugs = await fetch('/api/v1/snomed/search?q=paracetamol', {
  headers: { 'X-API-Key': 'dev-key-123' }
});

// 2. AI diagnosis
const diagnosis = await fetch('/api/v1/clinical-ai/diagnose', {
  method: 'POST',
  headers: { 
    'X-API-Key': 'dev-key-123',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    symptoms: ['fever', 'cough'],
    patient_age: 35,
    patient_gender: 'M'
  })
});

// 3. Get drug alternatives
const alternatives = await fetch(
  `/api/v1/snomed/brands/${snomedId}/alternatives`,
  { headers: { 'X-API-Key': 'dev-key-123' } }
);
```

---

## 📊 Data Flow Architecture

```
┌──────────────┐
│   Frontend   │ (React/Angular/Mobile App)
└──────┬───────┘
       │ HTTPS + API Key
       ↓
┌──────────────┐
│  FastAPI     │ (Port 8001)
│  - Auth      │
│  - Rate Limit│
│  - Logging   │
└──────┬───────┘
       │
       ├─→ Grok/Ollama (AI Diagnosis)
       │
       ├─→ PostgreSQL (89K+ drugs, ICD codes)
       │
       └─→ Redis (Caching, Rate Limiting)
```

---

## 🎯 Deployment Flow

### Development
```bash
./install.sh      # One-time setup
./start.sh        # Daily start
./test_all.sh     # Validate
```

### Production
```bash
# Option 1: Systemd
sudo systemctl start hms-api
sudo systemctl enable hms-api

# Option 2: Docker
docker-compose up -d

# Option 3: Kubernetes
kubectl apply -f k8s/deployment.yaml
```

---

## 🔐 Security Flow

```
Client Request
    ↓
API Key Validation (X-API-Key header)
    ↓
Rate Limiting (100 req/min per IP)
    ↓
Input Sanitization
    ↓
Business Logic
    ↓
Database Query (Parameterized)
    ↓
Response (JSON)
    ↓
Audit Log (who, what, when)
```

---

## 📈 Monitoring Flow

```
Application Logs → logs/server.log
    ↓
Error Tracking → logs/error.log
    ↓
Performance Metrics → /api/v1/health
    ↓
Database Stats → PostgreSQL logs
    ↓
Alerts → Email/Slack (if configured)
```

---

## 🚀 Quick Start Flow (New Developer)

```bash
# Day 1: Setup
git clone <repo>
cd data-machine
./install.sh
# ☕ Coffee break (5 mins)
# ✅ Done! Server running

# Day 2: Development
./start.sh              # Start server
curl http://localhost:8001/docs  # Explore API
./test_all.sh          # Run tests
./stop.sh              # Stop server

# Day 3: Integration
# Use API in your frontend
# Test with Postman/Swagger
# Deploy to production
```

---

## 💡 Best Practices

### 1. Always Use SNOMED Codes
```python
# ✅ Good
prescription = {
  "drug_snomed_id": 2430421000189104,
  "drug_name": "Crocin 500mg",
  "diagnosis_icd10": "J06.9"
}

# ❌ Bad
prescription = {
  "drug_name": "Crocin",  # No standard code
  "diagnosis": "fever"     # Not ICD-10
}
```

### 2. Use AI for Suggestions, Not Final Diagnosis
```python
# ✅ Good
ai_suggestion = get_ai_diagnosis(symptoms)
doctor_reviews(ai_suggestion)
doctor_confirms_diagnosis()

# ❌ Bad
ai_diagnosis = get_ai_diagnosis(symptoms)
auto_prescribe(ai_diagnosis)  # No human review!
```

### 3. Cache Frequently Used Data
```python
# ✅ Good - Cache drug search results
@cache(ttl=3600)
def search_drugs(query):
    return db.query(...)

# ❌ Bad - Query DB every time
def search_drugs(query):
    return db.query(...)  # Slow!
```

---

## 📞 Support Flow

```
Issue Occurs
    ↓
Check logs: tail -f logs/server.log
    ↓
Check status: ./status.sh
    ↓
Restart: ./restart.sh
    ↓
Still broken? Check DEPLOYMENT.md troubleshooting
    ↓
Still broken? Create GitHub issue
```
