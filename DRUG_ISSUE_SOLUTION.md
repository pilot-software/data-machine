# Issue: recommended_drugs Empty

## Problem
The `/diagnose-text` endpoint returns empty `recommended_drugs` array even though:
- ✅ Ollama returns specific drug names: `["ciprofloxacin", "ceftriaxone"]`
- ✅ Database has 1,382 ciprofloxacin brands
- ✅ Database has 2,411 ceftriaxone brands

## Root Cause
The improved prompt IS working - Ollama now returns specific drug names instead of "antibiotics".

However, the drugs aren't appearing in the response. Possible causes:
1. JSON parsing issue (LLM returns text before JSON)
2. ICD code format mismatch (N39.0 vs N390)
3. Code logic issue

## Solution

### Option 1: Use Better LLM (Recommended)
Replace llama2 with a medical-focused model:

```bash
# Install medical model
ollama pull medllama2

# Or use a larger general model
ollama pull llama2:13b
```

Update code:
```python
response = requests.post(
    'http://localhost:11434/api/generate',
    json={'model': 'medllama2', 'prompt': prompt, 'stream': False},  # Changed model
    timeout=60
)
```

### Option 2: Improve Prompt Further
```python
llm_prompt = f\"\"\"Medical diagnosis task. Patient: {prompt}

Return ONLY this JSON (no text before or after):
{{
  "symptoms": ["fever", "chills"],
  "primary_diagnosis": "Acute Pyelonephritis",
  "icd10_codes": ["N390"],
  "generic_drugs": ["ciprofloxacin", "ceftriaxone"],
  "confidence": "high"
}}

Rules:
- ICD codes WITHOUT dots (N390 not N39.0)
- Specific drug names (ciprofloxacin not antibiotics)
- JSON only, no explanation\"\"\"
```

### Option 3: Use AWS Bedrock or OpenAI
Set environment variable:
```bash
export OPENAI_API_KEY=your-key
```

The system will auto-detect and use OpenAI which gives better results.

## Testing

```bash
# Test with improved prompt
curl -X POST "http://localhost:8001/api/v1/clinical-ai/diagnose-text?prompt=acute%20pyelonephritis%20fever%20chills" \
  -H "X-API-Key: dev-key-123"
```

Expected output:
```json
{
  "recommended_drugs": [
    {
      "snomed_id": 2430421000189104,
      "brand_name": "Ciprofloxacin 500mg Tablet",
      "generic_name": "Ciprofloxacin",
      "supplier_name": "Cipla Ltd"
    }
  ]
}
```

## Current Status
- ✅ Prompt improved to request specific drugs
- ✅ Database has all required drugs
- ⏳ Need better LLM or further prompt tuning
- ⏳ Consider using OpenAI/Bedrock for production

## Recommendation
For production use, switch to:
1. **OpenAI GPT-4** - Best medical understanding
2. **AWS Bedrock Claude** - Good balance
3. **Ollama medllama2** - Free but needs fine-tuning
