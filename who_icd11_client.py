#!/usr/bin/env python3
"""
WHO ICD-11 API Client - Minimal implementation
"""

import requests
import json
import os
from typing import Dict, List, Optional

class WHOIcd11Client:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = "https://icdaccessmanagement.who.int/connect/token"
        self.api_base = "https://id.who.int/icd/release/11/2023-01/mms"
        self.access_token = None
    
    def get_access_token(self) -> str:
        """Get OAuth2 access token"""
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'icdapi_access',
            'grant_type': 'client_credentials'
        }
        
        response = requests.post(self.token_url, data=payload)
        response.raise_for_status()
        
        token_data = response.json()
        self.access_token = token_data['access_token']
        return self.access_token
    
    def search_codes(self, query: str, limit: int = 50) -> List[Dict]:
        """Search ICD-11 codes"""
        if not self.access_token:
            self.get_access_token()
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'API-Version': 'v2',
            'Accept-Language': 'en'
        }
        
        params = {
            'q': query,
            'subtreeFilterUsesFoundationDescendants': 'false',
            'includeKeywordResult': 'true',
            'useFlexisearch': 'false',
            'flatResults': 'false',
            'highlightingEnabled': 'false'
        }
        
        response = requests.get(f"{self.api_base}/search", headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        # Handle different response formats
        entities = data.get('destinationEntities', [])
        if isinstance(entities, str):
            return results
            
        for item in entities[:limit]:
            if isinstance(item, dict):
                title = item.get('title', '')
                if isinstance(title, dict):
                    title = title.get('@value', '')
                
                definition = item.get('definition', '')
                if isinstance(definition, dict):
                    definition = definition.get('@value', '')
                
                results.append({
                    'code': item.get('theCode', ''),
                    'title': title,
                    'url': item.get('@id', ''),
                    'chapter': item.get('chapter', ''),
                    'definition': definition
                })
        
        return results
    
    def get_code_details(self, code_url: str) -> Dict:
        """Get detailed information for a specific code"""
        if not self.access_token:
            self.get_access_token()
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'API-Version': 'v2',
            'Accept-Language': 'en'
        }
        
        response = requests.get(code_url, headers=headers)
        response.raise_for_status()
        
        return response.json()

def download_icd11_data():
    """Download real ICD-11 data using WHO API"""
    client_id = "f027b85b-e451-4a03-871a-d5e96778ffc1_9056b59a-973c-4e09-9190-e1a18a88f68b"
    client_secret = "hTgKi4F3Nh2kfNRt29xlGOIlkXv60pQBosynSy34LWM="
    
    client = WHOIcd11Client(client_id, client_secret)
    
    # Comprehensive medical terms for full ICD-11 coverage
    search_terms = [
        "diabetes", "hypertension", "pneumonia", "depression", "cancer", "heart disease", "stroke", "asthma", "arthritis", "infection",
        "fever", "pain", "injury", "fracture", "wound", "burn", "poisoning", "allergy", "anemia", "bleeding",
        "pregnancy", "birth", "congenital", "genetic", "syndrome", "disorder", "disease", "condition", "abnormal", "malformation",
        "kidney", "liver", "lung", "brain", "spine", "bone", "muscle", "skin", "eye", "ear",
        "tuberculosis", "malaria", "hepatitis", "influenza", "covid", "pneumonia", "sepsis", "meningitis", "encephalitis", "gastritis",
        "obesity", "malnutrition", "vitamin", "mineral", "metabolic", "endocrine", "hormone", "thyroid", "adrenal", "pituitary",
        "anxiety", "psychosis", "dementia", "autism", "adhd", "bipolar", "schizophrenia", "addiction", "substance", "alcohol",
        "epilepsy", "migraine", "headache", "seizure", "paralysis", "neuropathy", "sclerosis", "parkinson", "alzheimer", "huntington",
        "blindness", "deafness", "cataract", "glaucoma", "retina", "cornea", "hearing", "tinnitus", "vertigo", "balance",
        "arrhythmia", "infarction", "angina", "valve", "cardiomyopathy", "pericarditis", "endocarditis", "thrombosis", "embolism", "aneurysm",
        "bronchitis", "emphysema", "fibrosis", "apnea", "respiratory", "cough", "dyspnea", "pleural", "pneumothorax", "atelectasis",
        "gastroenteritis", "ulcer", "colitis", "crohn", "cirrhosis", "pancreatitis", "gallstone", "hernia", "obstruction", "perforation",
        "nephritis", "stones", "failure", "dialysis", "transplant", "cystitis", "prostate", "incontinence", "hematuria", "proteinuria",
        "osteoporosis", "scoliosis", "dislocation", "sprain", "strain", "tendon", "ligament", "cartilage", "joint", "vertebra",
        "eczema", "psoriasis", "dermatitis", "melanoma", "carcinoma", "sarcoma", "lymphoma", "leukemia", "tumor", "metastasis"
    ]
    
    all_codes = []
    
    print("🔄 Downloading real ICD-11 data from WHO API...")
    
    for term in search_terms:
        try:
            print(f"  Searching: {term}")
            results = client.search_codes(term, limit=50)
            all_codes.extend(results)
        except Exception as e:
            print(f"  ❌ Error searching {term}: {e}")
    
    # Remove duplicates
    unique_codes = {code['code']: code for code in all_codes if code['code']}
    final_codes = list(unique_codes.values())
    
    # Save to file
    os.makedirs('data', exist_ok=True)
    with open('data/icd11_who_api.json', 'w') as f:
        json.dump(final_codes, f, indent=2)
    
    print(f"✅ Downloaded {len(final_codes)} unique ICD-11 codes")
    return final_codes

if __name__ == "__main__":
    download_icd11_data()