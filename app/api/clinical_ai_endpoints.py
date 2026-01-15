"""
LLM-Powered Clinical Assistant
Supports: AWS Bedrock, OpenAI, Ollama, Groq, Grok
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy import text
from app.db.database import SessionLocal
from app.middleware.auth import verify_api_key
from app.services.safety_rules import safety_engine
from app.services.rxnorm_validator import validate_drugs_with_rxnorm
import json
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

router = APIRouter(
    prefix="/api/v1/clinical-ai",
    tags=["clinical-assistant"],
    dependencies=[Depends(verify_api_key)]
)

# Auto-detect available LLM
def detect_llm():
    # Force provider if set
    force_provider = os.getenv('FORCE_LLM_PROVIDER')
    if force_provider:
        return force_provider
    
    # Try Groq (fastest)
    if os.getenv('GROQ_API_KEY'):
        return "groq"
    
    # Try Grok
    if os.getenv('XAI_API_KEY'):
        return "grok"
    
    # Try Ollama (free, local)
    try:
        requests.get('http://localhost:11434/api/tags', timeout=1)
        return "ollama"
    except:
        pass
    
    # Try AWS Bedrock
    try:
        import boto3
        boto3.client('bedrock-runtime', region_name='us-east-1')
        return "bedrock"
    except:
        pass
    
    # Try OpenAI
    if os.getenv('OPENAI_API_KEY'):
        return "openai"
    
    return None

LLM_PROVIDER = detect_llm()


class SymptomRequest(BaseModel):
    symptoms: List[str] = Field(..., example=["cough", "headache", "mild fever"])
    patient_age: Optional[int] = Field(None, example=35)
    patient_gender: Optional[str] = Field(None, example="M")
    location: Optional[str] = Field(None, example="Mumbai")
    duration: Optional[str] = Field(None, example="3 days")


def call_llm(prompt: str) -> str:
    """Call LLM (Groq, Grok, Ollama, Bedrock, OpenAI) - NO FALLBACK"""
    
    if LLM_PROVIDER == "groq":
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={'Authorization': f'Bearer {os.getenv("GROQ_API_KEY")}'},
            json={
                'model': 'llama-3.3-70b-versatile',
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.3
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        raise HTTPException(500, f"Groq failed: {response.status_code}")
    
    elif LLM_PROVIDER == "grok":
        response = requests.post(
            'https://api.x.ai/v1/chat/completions',
            headers={'Authorization': f'Bearer {os.getenv("XAI_API_KEY")}'},
            json={
                'model': 'grok-beta',
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.3
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        raise HTTPException(500, f"Grok failed: {response.status_code}")
    
    elif LLM_PROVIDER == "ollama":
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={'model': 'llama2', 'prompt': prompt, 'stream': False},
            timeout=60
        )
        if response.status_code == 200:
            return response.json()['response']
        raise HTTPException(500, f"Ollama failed: {response.status_code}")
    
    elif LLM_PROVIDER == "bedrock":
        import boto3
        bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        return json.loads(response['body'].read())['content'][0]['text']
    
    elif LLM_PROVIDER == "openai":
        import openai
        openai.api_key = os.getenv('OPENAI_API_KEY')
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content
    
    raise HTTPException(503, "No LLM available. Set GROQ_API_KEY, XAI_API_KEY, or install Ollama")


@router.post("/diagnose")
async def ai_diagnose(request: SymptomRequest):
    """AI-powered diagnosis with free Ollama support"""
    
    db = SessionLocal()
    
    try:
        prompt = f"""You are a medical diagnostic AI. Analyze the patient and provide diagnosis.

Patient: {request.patient_age} years old, {request.patient_gender}, Duration: {request.duration}
Symptoms: {', '.join(request.symptoms)}

⚠️ CRITICAL: You MUST respond in ENGLISH ONLY, even if symptoms are in Hindi or other languages.

You MUST return ONLY a JSON object with this EXACT structure (no other text):
{{
  "primary_diagnosis": "disease name IN ENGLISH",
  "icd10_codes": ["CODE1", "CODE2"],
  "confidence": "high or medium or low",
  "reasoning": "why this diagnosis IN ENGLISH",
  "differential_diagnoses": ["alternative1 IN ENGLISH", "alternative2 IN ENGLISH"],
  "recommended_tests": ["test1 IN ENGLISH", "test2 IN ENGLISH"],
  "red_flags": ["warning1 IN ENGLISH", "warning2 IN ENGLISH"],
  "generic_drugs": ["drug1 IN ENGLISH", "drug2 IN ENGLISH", "drug3 IN ENGLISH"]
}}

IMPORTANT:
- ALL TEXT MUST BE IN ENGLISH (translate if needed)
- ICD codes: NO DOTS (write E11 not E.11, I10 not I.10)
- Drugs: ONLY generic names in ENGLISH (metformin NOT मेटफॉर्मिन)
- Be specific based on the symptoms

Return ONLY the JSON object:"""

        llm_response = call_llm(prompt)
        
        # Parse response - extract JSON from text
        if "```json" in llm_response:
            llm_response = llm_response.split("```json")[1].split("```")[0]
        elif "```" in llm_response:
            llm_response = llm_response.split("```")[1].split("```")[0]
        
        if "{" in llm_response:
            start = llm_response.find("{")
            end = llm_response.rfind("}") + 1
            llm_response = llm_response[start:end]
        
        llm_analysis = json.loads(llm_response.strip())
        
        # Prepare safety context
        safety_context = {
            "prompt": f"Patient: {request.patient_age} years, {request.patient_gender}, Symptoms: {', '.join(request.symptoms)}",
            "primary_diagnosis": llm_analysis.get("primary_diagnosis", ""),
            "red_flags": llm_analysis.get("red_flags", []),
            "differential_diagnoses": llm_analysis.get("differential_diagnoses", [])
        }
        
        # Get drugs from database
        raw_drugs = []
        for generic in llm_analysis.get("generic_drugs", [])[:5]:
            drug_names = []
            if "(" in generic:
                import re
                matches = re.findall(r'\b([A-Z][a-z]+(?:cillin|mycin|floxacin|azole|prim|furantoin|cycline))\b', generic)
                drug_names.extend([m.lower() for m in matches])
            else:
                drug_names.append(generic.lower())
            
            for drug_name in drug_names:
                drugs = db.execute(text("""
                    SELECT b.snomed_id, b.brand_name, g.generic_name, s.supplier_name
                    FROM snomed_brands b
                    JOIN snomed_generics g ON b.generic_id = g.snomed_id
                    LEFT JOIN snomed_suppliers s ON b.supplier_id = s.snomed_id
                    WHERE LOWER(g.generic_name) LIKE :generic 
                      AND b.active = TRUE
                      AND b.route_of_administration = 'oral'
                    LIMIT 2
                """), {"generic": f"%{drug_name}%"}).fetchall()
                
                for drug in drugs:
                    raw_drugs.append({
                        "snomed_id": drug.snomed_id,
                        "brand_name": drug.brand_name,
                        "generic_name": drug.generic_name,
                        "supplier_name": drug.supplier_name
                    })
                
                if drugs:
                    break
        
        # Apply safety filters
        icd_codes = llm_analysis.get("icd10_codes", [])
        filtered_drugs, corrected_icd_codes, safety_results = safety_engine.apply_filters(
            raw_drugs, icd_codes, safety_context
        )
        
        # RxNorm validation (drug interactions, contraindications)
        patient_age = request.patient_age or 35
        rxnorm_validation = validate_drugs_with_rxnorm(
            filtered_drugs, patient_age, llm_analysis.get("primary_diagnosis", ""), db
        )
        safety_results["warnings"].extend(rxnorm_validation["warnings"])
        safety_results["drug_interactions"] = rxnorm_validation["interactions"]
        
        # Validate corrected ICD codes
        diagnosis_suggestions = []
        for icd_code in corrected_icd_codes[:3]:
            normalized_code = icd_code.replace(".", "")
            
            icd_result = db.execute(
                text("SELECT code, term FROM icd10_codes WHERE code = :code"),
                {"code": normalized_code}
            ).fetchone()
            
            if icd_result:
                diagnosis_suggestions.append({
                    "condition": llm_analysis["primary_diagnosis"],
                    "icd10_code": icd_result.code,
                    "icd10_description": icd_result.term,
                    "confidence": llm_analysis["confidence"],
                    "reasoning": llm_analysis["reasoning"]
                })
        
        return {
            "query": ", ".join(request.symptoms),
            "llm_provider": LLM_PROVIDER,
            "diagnosis_suggestions": diagnosis_suggestions,
            "differential_diagnoses": llm_analysis.get("differential_diagnoses", []),
            "recommended_drugs": filtered_drugs,
            "additional_tests": llm_analysis.get("recommended_tests", []),
            "red_flags": llm_analysis.get("red_flags", []),
            "safety_filters_applied": {
                "rules_triggered": safety_results["rules_triggered"],
                "drugs_excluded": len(raw_drugs) - len(filtered_drugs),
                "warnings": safety_results["warnings"],
                "antidotes_recommended": safety_results.get("antidotes_recommended", []),
                "drug_interactions": safety_results.get("drug_interactions", [])
            }
        }
        
    finally:
        db.close()


@router.post("/diagnose-text")
async def ai_diagnose_text(prompt: str):
    """Natural language diagnosis - just describe symptoms"""
    
    db = SessionLocal()
    
    try:
        llm_prompt = f"""You are a Clinical Decision Support System. Parse patient complaint into structured JSON.

Patient complaint: "{prompt}"

⚠️ CRITICAL RULES:
1. Extract symptoms accurately from the complaint (translate if non-English)
2. Diagnosis MUST match the extracted symptoms only
3. Do NOT invent symptoms not mentioned
4. Respond in English

### OUTPUT SCHEMA:
{{
  "primary_diagnosis": "disease name matching the symptoms",
  "icd10_codes": ["CODE1", "CODE2"],
  "extracted_symptoms": ["symptom1", "symptom2"],
  "differential_diagnoses": ["alternative1", "alternative2"],
  "generic_drugs": ["drug1", "drug2"],
  "red_flags": ["warning1", "warning2"],
  "clinical_rationale": "why these drugs for THIS diagnosis",
  "recommended_tests": ["test1", "test2"]
}}

RULES:
- ICD codes: NO DOTS (J06 not J.06)
- Drugs: Generic names ONLY

Return ONLY JSON:"""

        llm_response = call_llm(llm_prompt)
        
        # JSON SANITIZATION: Remove control characters for multilingual support
        import re
        llm_response = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', llm_response)
        
        # Parse response - extract JSON from text
        if "```json" in llm_response:
            llm_response = llm_response.split("```json")[1].split("```")[0]
        elif "```" in llm_response:
            llm_response = llm_response.split("```")[1].split("```")[0]
        
        if "{" in llm_response:
            start = llm_response.find("{")
            end = llm_response.rfind("}") + 1
            llm_response = llm_response[start:end]
        
        llm_analysis = json.loads(llm_response.strip())
        
        # Prepare safety context
        safety_context = {
            "prompt": prompt,
            "primary_diagnosis": llm_analysis.get("primary_diagnosis", ""),
            "red_flags": llm_analysis.get("red_flags", []),
            "differential_diagnoses": llm_analysis.get("differential_diagnoses", [])
        }
        
        # Get drugs from database
        raw_drugs = []
        for generic in llm_analysis.get("generic_drugs", [])[:5]:
            drugs = db.execute(text("""
                SELECT b.snomed_id, b.brand_name, g.generic_name, s.supplier_name
                FROM snomed_brands b
                JOIN snomed_generics g ON b.generic_id = g.snomed_id
                LEFT JOIN snomed_suppliers s ON b.supplier_id = s.snomed_id
                WHERE LOWER(g.generic_name) LIKE :generic 
                  AND b.active = TRUE
                  AND b.route_of_administration = 'oral'
                LIMIT 2
            """), {"generic": f"%{generic.lower()}%"}).fetchall()
            
            for drug in drugs:
                raw_drugs.append({
                    "snomed_id": drug.snomed_id,
                    "brand_name": drug.brand_name,
                    "generic_name": drug.generic_name,
                    "supplier_name": drug.supplier_name
                })
        
        # Apply safety filters
        icd_codes = llm_analysis.get("icd10_codes", [])
        filtered_drugs, corrected_icd_codes, safety_results = safety_engine.apply_filters(
            raw_drugs, icd_codes, safety_context
        )
        
        # RxNorm validation
        import re
        age_match = re.search(r'(\d+)\s*(?:year|yr|age)', prompt.lower())
        patient_age = int(age_match.group(1)) if age_match else 35
        
        rxnorm_validation = validate_drugs_with_rxnorm(
            filtered_drugs, patient_age, llm_analysis.get("primary_diagnosis", ""), db
        )
        safety_results["warnings"].extend(rxnorm_validation["warnings"])
        safety_results["drug_interactions"] = rxnorm_validation["interactions"]
        
        # Validate corrected ICD codes
        diagnosis_suggestions = []
        for icd_code in corrected_icd_codes[:3]:
            normalized_code = icd_code.replace(".", "")
            
            icd_result = db.execute(
                text("SELECT code, term FROM icd10_codes WHERE code = :code"),
                {"code": normalized_code}
            ).fetchone()
            
            if icd_result:
                diagnosis_suggestions.append({
                    "condition": llm_analysis.get("primary_diagnosis", "Unknown"),
                    "icd10_code": icd_result.code,
                    "icd10_description": icd_result.term,
                    "confidence": llm_analysis.get("confidence", "medium"),
                    "reasoning": llm_analysis.get("reasoning", "")
                })
        
        return {
            "original_prompt": prompt,
            "extracted_symptoms": llm_analysis.get("extracted_symptoms", []),
            "duration": llm_analysis.get("duration", ""),
            "primary_diagnosis": llm_analysis.get("primary_diagnosis", ""),
            "clinical_rationale": llm_analysis.get("clinical_rationale", ""),
            "llm_provider": LLM_PROVIDER,
            "diagnosis_suggestions": diagnosis_suggestions,
            "differential_diagnoses": llm_analysis.get("differential_diagnoses", []),
            "recommended_drugs": filtered_drugs,
            "additional_tests": llm_analysis.get("recommended_tests", []),
            "red_flags": llm_analysis.get("red_flags", []),
            "safety_filters_applied": {
                "rules_triggered": safety_results["rules_triggered"],
                "drugs_excluded": len(raw_drugs) - len(filtered_drugs),
                "warnings": safety_results["warnings"],
                "antidotes_recommended": safety_results.get("antidotes_recommended", []),
                "drug_interactions": safety_results.get("drug_interactions", [])
            }
        }
        
    finally:
        db.close()


@router.get("/status")
async def llm_status():
    """Check LLM provider status"""
    return {
        "provider": LLM_PROVIDER,
        "available": True,
        "message": f"Using {LLM_PROVIDER} for AI diagnosis"
    }
