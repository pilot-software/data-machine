"""
LLM-Powered Clinical Assistant
Supports: AWS Bedrock, OpenAI, Ollama (FREE), Demo mode
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy import text
from app.db.database import SessionLocal
from app.middleware.auth import verify_api_key
import json
import os
import requests

router = APIRouter(
    prefix="/api/v1/clinical-ai",
    tags=["clinical-assistant"],
    dependencies=[Depends(verify_api_key)]
)

# Auto-detect available LLM
def detect_llm():
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
    
    return "demo"

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

You MUST return ONLY a JSON object with this EXACT structure (no other text):
{{
  "primary_diagnosis": "disease name",
  "icd10_codes": ["CODE1", "CODE2"],
  "confidence": "high or medium or low",
  "reasoning": "why this diagnosis",
  "differential_diagnoses": ["alternative1", "alternative2"],
  "recommended_tests": ["test1", "test2"],
  "red_flags": ["warning1", "warning2"],
  "generic_drugs": ["drug1", "drug2", "drug3"]
}}

IMPORTANT:
- ICD codes: NO DOTS (write A09 not A.09, I10 not I.10)
- Drugs: ONLY generic names (ondansetron NOT anti-nausea)
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
        
        # Validate ICD codes - handle both formats (N39.0 -> N390)
        diagnosis_suggestions = []
        for icd_code in llm_analysis.get("icd10_codes", [])[:3]:
            # Normalize ICD code - remove dots
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
        
        # Get SNOMED drugs - extract simple drug names from complex strings
        recommended_drugs = []
        for generic in llm_analysis.get("generic_drugs", [])[:5]:
            # Extract simple drug name from complex strings like "Antibiotics (such as Augmentin or Ceftriaxone)"
            drug_names = []
            if "(" in generic:
                # Extract names from parentheses
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
                    WHERE LOWER(g.generic_name) LIKE :generic AND b.active = TRUE
                    LIMIT 2
                """), {"generic": f"%{drug_name}%"}).fetchall()
                
                for drug in drugs:
                    recommended_drugs.append({
                        "snomed_id": drug.snomed_id,
                        "brand_name": drug.brand_name,
                        "generic_name": drug.generic_name,
                        "supplier_name": drug.supplier_name
                    })
                
                if drugs:  # Stop after finding matches
                    break
        
        return {
            "query": ", ".join(request.symptoms),
            "llm_provider": LLM_PROVIDER,
            "diagnosis_suggestions": diagnosis_suggestions,
            "differential_diagnoses": llm_analysis.get("differential_diagnoses", []),
            "recommended_drugs": recommended_drugs,
            "additional_tests": llm_analysis.get("recommended_tests", []),
            "red_flags": llm_analysis.get("red_flags", [])
        }
        
    finally:
        db.close()


@router.post("/diagnose-text")
async def ai_diagnose_text(prompt: str):
    """Natural language diagnosis - just describe symptoms"""
    
    db = SessionLocal()
    
    try:
        llm_prompt = f"""You are a medical diagnostic AI. Analyze the patient's complaint and provide diagnosis.

Patient complaint: "{prompt}"

You MUST return ONLY a JSON object with this EXACT structure (no other text):
{{
  "symptoms": ["list", "of", "symptoms"],
  "duration": "time period",
  "primary_diagnosis": "most likely disease name",
  "icd10_codes": ["CODE1", "CODE2"],
  "confidence": "high or medium or low",
  "reasoning": "why this diagnosis",
  "differential_diagnoses": ["alternative1", "alternative2"],
  "recommended_tests": ["test1", "test2"],
  "red_flags": ["warning1", "warning2"],
  "generic_drugs": ["drug1", "drug2", "drug3"]
}}

IMPORTANT:
- ICD codes: NO DOTS (write A09 not A.09, J069 not J06.9)
- Drugs: ONLY generic names (ondansetron NOT anti-nausea)
- Be specific based on the symptoms described

Return ONLY the JSON object:"""

        llm_response = call_llm(llm_prompt)
        
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
        
        diagnosis_suggestions = []
        for icd_code in llm_analysis.get("icd10_codes", [])[:3]:
            # Normalize ICD code - remove dots
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
        
        recommended_drugs = []
        for generic in llm_analysis.get("generic_drugs", [])[:5]:
            drugs = db.execute(text("""
                SELECT b.snomed_id, b.brand_name, g.generic_name, s.supplier_name
                FROM snomed_brands b
                JOIN snomed_generics g ON b.generic_id = g.snomed_id
                LEFT JOIN snomed_suppliers s ON b.supplier_id = s.snomed_id
                WHERE LOWER(g.generic_name) LIKE :generic AND b.active = TRUE
                LIMIT 2
            """), {"generic": f"%{generic.lower()}%"}).fetchall()
            
            for drug in drugs:
                recommended_drugs.append({
                    "snomed_id": drug.snomed_id,
                    "brand_name": drug.brand_name,
                    "generic_name": drug.generic_name,
                    "supplier_name": drug.supplier_name
                })
        
        return {
            "original_prompt": prompt,
            "extracted_symptoms": llm_analysis.get("symptoms", []),
            "duration": llm_analysis.get("duration", ""),
            "llm_provider": LLM_PROVIDER,
            "diagnosis_suggestions": diagnosis_suggestions,
            "differential_diagnoses": llm_analysis.get("differential_diagnoses", []),
            "recommended_drugs": recommended_drugs,
            "additional_tests": llm_analysis.get("recommended_tests", []),
            "red_flags": llm_analysis.get("red_flags", [])
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
