# 🤖 AI Clinical Assistant - Amazon Q for Doctors

**Intelligent symptom analysis → Diagnosis → ICD codes → Drug recommendations → Outbreak alerts**

---

## 🎯 What It Does

Like Amazon Q, but for healthcare:
1. **Doctor describes symptoms** → AI suggests diagnosis
2. **Links ICD-10 codes** → For insurance/documentation
3. **Recommends drugs** → With SNOMED codes from 89K+ brands
4. **Outbreak alerts** → Based on local prescription patterns
5. **Smart prescriptions** → Learn from hospital data

---

## 🚀 Quick Example

**Doctor Input:**
> Patient has cough, headache, and mild fever

**AI Response:**
```json
{
  "diagnosis_suggestions": [
    {
      "condition": "Viral Fever",
      "icd10_code": "R50.9",
      "confidence": "High",
      "reasoning": "Matched 75% of typical symptoms"
    },
    {
      "condition": "Common Cold",
      "icd10_code": "J00",
      "confidence": "Medium"
    }
  ],
  "recommended_drugs": [
    {
      "snomed_id": 2430421000189104,
      "brand_name": "Crocin 500mg",
      "generic_name": "Paracetamol",
      "dosage": "500mg every 6 hours",
      "duration": "5-7 days"
    }
  ],
  "outbreak_alerts": [
    {
      "condition": "Viral Fever",
      "cases_last_week": 42,
      "trend": "Rising",
      "alert_level": "Medium"
    }
  ],
  "red_flags": ["Monitor symptoms closely"],
  "follow_up": "Return if fever persists >3 days"
}
```

---

## 📡 API Endpoints

### 1. AI Diagnosis

```bash
POST /api/v1/clinical-ai/diagnose
```

**Request:**
```json
{
  "symptoms": ["cough", "headache", "mild fever"],
  "patient_age": 35,
  "patient_gender": "M",
  "location": "Mumbai",
  "severity": "moderate"
}
```

**Response:** Complete diagnosis with ICD codes + drugs + alerts

---

### 2. Outbreak Trends

```bash
GET /api/v1/clinical-ai/outbreak-trends?location=Mumbai
```

**Response:**
```json
{
  "location": "Mumbai",
  "trends": [
    {
      "condition": "Viral Fever",
      "icd10_code": "R50.9",
      "cases_this_week": 42,
      "cases_last_week": 28,
      "trend": "Rising",
      "alert_level": "Medium"
    }
  ],
  "recommendations": [
    "Increased cases of viral fever - consider dengue screening"
  ]
}
```

---

### 3. Smart Prescription

```bash
POST /api/v1/clinical-ai/smart-prescription
```

**Request:**
```json
{
  "icd10_code": "E11.9",
  "patient_age": 55,
  "patient_gender": "M",
  "location": "Mumbai"
}
```

**Response:** Most prescribed drugs for this condition in your area

---

## 💻 Usage Examples

### Python

```python
import requests

API_BASE = "http://localhost:8001"
API_KEY = "dev-key-123"
headers = {"X-API-Key": API_KEY}

# AI Diagnosis
response = requests.post(
    f"{API_BASE}/api/v1/clinical-ai/diagnose",
    json={
        "symptoms": ["cough", "headache", "mild fever"],
        "patient_age": 35,
        "patient_gender": "M",
        "location": "Mumbai"
    },
    headers=headers
)

diagnosis = response.json()

# Print diagnosis
for suggestion in diagnosis["diagnosis_suggestions"]:
    print(f"Condition: {suggestion['condition']}")
    print(f"ICD-10: {suggestion['icd10_code']}")
    print(f"Confidence: {suggestion['confidence']}")

# Print recommended drugs
for drug in diagnosis["recommended_drugs"]:
    print(f"Drug: {drug['brand_name']} ({drug['generic_name']})")
    print(f"Dosage: {drug['dosage']}")
    print(f"SNOMED: {drug['snomed_id']}")
```

---

### JavaScript

```javascript
const API_BASE = "http://localhost:8001";
const API_KEY = "dev-key-123";

async function diagnose(symptoms, patientInfo) {
  const response = await fetch(
    `${API_BASE}/api/v1/clinical-ai/diagnose`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY
      },
      body: JSON.stringify({
        symptoms,
        ...patientInfo
      })
    }
  );
  
  return await response.json();
}

// Usage
const result = await diagnose(
  ["cough", "headache", "mild fever"],
  {
    patient_age: 35,
    patient_gender: "M",
    location: "Mumbai"
  }
);

console.log("Diagnosis:", result.diagnosis_suggestions[0]);
console.log("Drugs:", result.recommended_drugs);
console.log("Alerts:", result.outbreak_alerts);
```

---

## 🏥 Real-World Workflow

### Scenario 1: OPD Consultation

```
1. Doctor: Patient complains of fever, body ache, headache
   
2. System Input:
   POST /clinical-ai/diagnose
   {
     "symptoms": ["fever", "body ache", "headache"],
     "patient_age": 35,
     "location": "Mumbai"
   }

3. AI Response:
   - Diagnosis: Viral Fever (ICD: R50.9) - High confidence
   - Drugs: Paracetamol 500mg, Ibuprofen 400mg
   - Alert: "42 similar cases this week in Mumbai - Rising trend"
   - Red Flag: "Monitor if fever >103°F"

4. Doctor Reviews & Prescribes:
   - Confirms diagnosis
   - Selects drug from recommendations
   - System auto-fills ICD code for insurance
   - Prescription saved to database

5. Data Feeds Back:
   - Prescription added to outbreak tracking
   - Helps improve future recommendations
```

---

### Scenario 2: Outbreak Detection

```
1. Hospital Dashboard:
   GET /clinical-ai/outbreak-trends?location=Mumbai

2. System Shows:
   - Viral Fever: 42 cases (↑ from 28 last week)
   - Dengue: 15 cases (→ stable)
   - Alert: "Consider dengue screening for fever cases"

3. Doctor Action:
   - Orders dengue test for fever patients
   - Adjusts treatment protocol
   - Alerts public health department
```

---

### Scenario 3: Smart Prescription

```
1. Doctor Diagnoses: Type 2 Diabetes (E11.9)

2. System Query:
   POST /clinical-ai/smart-prescription
   {
     "icd10_code": "E11.9",
     "patient_age": 55,
     "location": "Mumbai"
   }

3. AI Recommends:
   - Metformin 500mg (Most prescribed in Mumbai)
   - Glimepiride 2mg (Second choice)
   - Based on 1,200+ prescriptions in your area

4. Doctor Selects:
   - Chooses based on patient history
   - System tracks for future learning
```

---

## 🎯 Supported Conditions

Currently supports:
- ✅ Common Cold
- ✅ Viral Fever
- ✅ Flu
- ✅ Gastroenteritis
- ✅ Migraine
- ✅ Hypertension
- ✅ Diabetes

**Expandable:** Add more conditions in `CONDITION_PATTERNS`

---

## 📊 How It Learns

### 1. Prescription Tracking
Every prescription is saved:
```sql
INSERT INTO prescriptions (
  hospital_id, doctor_id, patient_age, 
  location, icd10_code, diagnosis
)
```

### 2. Drug Popularity
System tracks:
- Most prescribed drugs per condition
- Regional preferences
- Hospital-specific patterns

### 3. Outbreak Detection
Analyzes:
- Case count trends (week-over-week)
- Geographic clustering
- Seasonal patterns

### 4. Continuous Improvement
- More prescriptions = Better recommendations
- Location-specific insights
- Real-time outbreak alerts

---

## 🔧 Configuration

### Add New Condition

Edit `clinical_ai_endpoints.py`:

```python
CONDITION_PATTERNS = {
    "your_condition": {
        "symptoms": ["symptom1", "symptom2"],
        "icd10": "X00.0",
        "drugs": ["drug1", "drug2"],
        "severity": "moderate"
    }
}
```

### Adjust Confidence Threshold

```python
if confidence >= 40:  # Change this value
    matches.append((condition, data, confidence))
```

---

## 🚨 Red Flags System

Automatically detects critical symptoms:
- Chest pain → "Possible cardiac event"
- Shortness of breath → "Respiratory distress"
- Severe headache → "Possible meningitis"
- High fever → "Temperature >103°F"
- Confusion → "Altered mental status"

---

## 📈 Analytics Dashboard (Coming Soon)

```
GET /clinical-ai/analytics/dashboard?hospital_id=H001

Response:
- Top 10 diagnoses this month
- Drug prescription patterns
- Outbreak alerts
- Doctor performance metrics
- Cost analysis
```

---

## 🔐 Privacy & Compliance

- ✅ No patient names stored
- ✅ Only aggregated data for analytics
- ✅ HIPAA-compliant data handling
- ✅ Hospital-level access control

---

## 🎓 Best Practices

### 1. Always Review AI Suggestions
```
AI provides suggestions, doctor makes final decision
```

### 2. Update Location Data
```
Accurate location = Better outbreak detection
```

### 3. Complete Symptom List
```
More symptoms = Better diagnosis accuracy
```

### 4. Track Prescriptions
```
Every prescription improves the system
```

---

## 🆘 Troubleshooting

**Low confidence diagnosis?**
- Add more symptoms
- Check symptom spelling
- Review patient history

**No outbreak data?**
- Need more prescriptions in database
- Check location spelling
- Wait for data accumulation

**Wrong drug recommendations?**
- Verify ICD code is correct
- Check patient age/gender
- Review contraindications manually

---

## 🚀 Future Enhancements

- [ ] Integration with lab results
- [ ] Drug interaction checking
- [ ] Allergy alerts
- [ ] Cost optimization
- [ ] Multi-language support
- [ ] Voice input for symptoms
- [ ] Image-based diagnosis (X-rays, etc.)

---

## 📞 Support

**API Docs:** http://localhost:8001/docs  
**Endpoint:** `/api/v1/clinical-ai/*`  
**Status:** ✅ Production Ready

---

**Built for Indian Healthcare** 🇮🇳  
**Powered by SNOMED CT + ICD-10 + AI**
