# 🔄 Flow: /api/v1/clinical-ai/diagnose-text

## Complete Request Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. CLIENT REQUEST                                                │
│ POST /api/v1/clinical-ai/diagnose-text?prompt=dry%20cough       │
│ Headers: X-API-Key: dev-key-123                                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. MIDDLEWARE LAYER                                              │
│ ├─ Auth: verify_api_key() - Check API key validity              │
│ ├─ Rate Limiter: Check request limits (100/min)                 │
│ └─ Audit Logger: Log request details                            │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. ENDPOINT: ai_diagnose_text()                                  │
│ File: app/api/clinical_ai_endpoints.py                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. LLM PROMPT CONSTRUCTION                                       │
│ ├─ Input: "dry cough"                                            │
│ ├─ Build structured prompt for LLM                               │
│ └─ Request JSON schema with specific fields                     │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. LLM CALL (Groq/Ollama)                                        │
│ Function: call_llm(prompt)                                       │
│ ├─ Provider: Groq (openai/gpt-oss-120b)                         │
│ ├─ Temperature: 0.3 (deterministic)                              │
│ └─ Timeout: 60 seconds                                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. LLM RESPONSE PARSING                                          │
│ ├─ Extract JSON from response                                    │
│ ├─ Parse fields:                                                 │
│ │   • primary_diagnosis: "Acute bronchitis"                      │
│ │   • extracted_symptoms: ["dry cough"]                          │
│ │   • icd10_codes: ["J20"]                                       │
│ │   • generic_drugs: ["dextromethorphan", "paracetamol"]         │
│ │   • differential_diagnoses: ["Pneumonia", "Asthma"]            │
│ │   • red_flags: ["Severe difficulty breathing"]                │
│ └─ Sanitize: Remove control characters                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. DRUG SEARCH (SNOMED Database)                                 │
│ Function: get_drugs_for_symptoms(db, symptoms, diagnosis)        │
│ File: app/services/therapeutic_search.py                         │
│                                                                   │
│ Step 7a: Symptom-to-Ingredient Mapping                           │
│ ├─ Input: ["dry cough"]                                          │
│ ├─ Mapping: "cough" → ["dextromethorphan", "guaifenesin"]       │
│ └─ Evidence-based hardcoded mapping                              │
│                                                                   │
│ Step 7b: Database Query (per ingredient)                         │
│ ├─ Query: SELECT FROM snomed_brands b                            │
│ │         JOIN snomed_generics g ON b.generic_id = g.snomed_id  │
│ │         WHERE LOWER(g.generic_name) LIKE '%dextromethorphan%' │
│ │         AND b.active = TRUE                                    │
│ │         AND b.route_of_administration = 'oral'                 │
│ │         LIMIT 2                                                │
│ └─ Returns: 2 brands per ingredient                              │
│                                                                   │
│ Step 7c: Deduplication                                            │
│ └─ Remove duplicate SNOMED IDs, return top 5 unique drugs       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. SAFETY FILTERS (Optional - if implemented)                    │
│ Function: safety_engine.apply_filters()                          │
│ File: app/services/safety_rules.py                               │
│ ├─ Check contraindications                                       │
│ ├─ Validate dosages                                              │
│ └─ Apply exclusion rules                                         │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 9. ICD-10 VALIDATION                                             │
│ ├─ Normalize ICD codes (remove dots)                             │
│ ├─ Query: SELECT code, term FROM icd10_codes WHERE code = 'J20' │
│ └─ Build diagnosis_suggestions with validated ICD codes         │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 10. RESPONSE CONSTRUCTION                                        │
│ {                                                                 │
│   "original_prompt": "dry cough",                                │
│   "extracted_symptoms": ["dry cough"],                           │
│   "primary_diagnosis": "Acute bronchitis",                       │
│   "clinical_rationale": "...",                                   │
│   "llm_provider": "groq",                                        │
│   "diagnosis_suggestions": [{                                    │
│     "condition": "Acute bronchitis",                             │
│     "icd10_code": "J20",                                         │
│     "icd10_description": "Acute bronchitis"                      │
│   }],                                                            │
│   "recommended_drugs": [{                                        │
│     "snomed_id": 2792441000189107,                               │
│     "brand_name": "CGX-Tus (dextromethorphan...) 10 mg/5 ml",   │
│     "generic_name": "Dextromethorphan hydrobromide 10 mg/5 mL", │
│     "supplier_name": "Caregenex Healthcare Private Limited"      │
│   }],                                                            │
│   "differential_diagnoses": ["Pneumonia", "Asthma"],            │
│   "additional_tests": ["Chest X-ray"],                          │
│   "red_flags": ["Severe difficulty breathing"]                  │
│ }                                                                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 11. RESPONSE TO CLIENT                                           │
│ Status: 200 OK                                                   │
│ Content-Type: application/json                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Components

### 1. **LLM Integration** (`call_llm()`)
- **Purpose**: Convert natural language to structured medical data
- **Providers**: Groq (primary), Ollama, Grok, AWS Bedrock, OpenAI
- **Output**: JSON with diagnosis, symptoms, ICD codes, drug suggestions

### 2. **Therapeutic Search** (`get_drugs_for_symptoms()`)
- **Purpose**: Find appropriate drugs from SNOMED database
- **Method**: Symptom → Ingredient mapping → Database query
- **Data Source**: 89,446 Indian drug brands in PostgreSQL
- **Key**: Uses `generic_name` field (not `therapeutic_role` - mostly empty)

### 3. **Database Tables Used**
```sql
snomed_brands        -- 89,446 brand products
snomed_generics      -- 9,869 generic formulations  
snomed_suppliers     -- 7,934 manufacturers
icd10_codes          -- 71,704 diagnosis codes
```

### 4. **Symptom-to-Ingredient Mapping** (Evidence-Based)
```python
{
    "cough": ["dextromethorphan", "guaifenesin", "bromhexine"],
    "fever": ["paracetamol", "ibuprofen"],
    "pain": ["paracetamol", "ibuprofen", "diclofenac"],
    "allergy": ["cetirizine", "levocetirizine"],
    # ... more mappings
}
```

---

## Data Flow Diagram

```
User Input
    ↓
LLM (Groq) → Structured JSON
    ↓
Symptoms Extracted → ["dry cough"]
    ↓
Symptom Mapping → ["dextromethorphan", "guaifenesin"]
    ↓
SNOMED Database Query → Find brands with these ingredients
    ↓
Filter & Deduplicate → Top 5 unique drugs
    ↓
ICD-10 Validation → Verify diagnosis codes
    ↓
JSON Response → Return to client
```

---

## Performance Metrics

- **LLM Call**: ~2-5 seconds (Groq)
- **Database Query**: ~50-200ms per ingredient
- **Total Response Time**: ~3-6 seconds
- **Accuracy**: Depends on LLM + symptom mapping quality

---

## Limitations & Improvements

### Current Limitations:
1. **Hardcoded symptom mapping** - Not dynamic
2. **therapeutic_role field empty** - Can't use SNOMED's built-in classification
3. **No dosage intelligence** - Returns all formulations
4. **LLM hallucination risk** - May suggest wrong drugs

### Potential Improvements:
1. ✅ Use ICD-10 codes to map to drug classes
2. ✅ Populate therapeutic_role from external sources
3. ✅ Add dosage filtering (prefer safe OTC doses)
4. ✅ Implement safety rules engine
5. ✅ Cache common symptom-drug mappings
