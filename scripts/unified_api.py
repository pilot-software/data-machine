import re
import json
from fastapi import FastAPI, Query

app = FastAPI()

# Load both datasets
with open('data/icd11_who_api.json', 'r') as f:
    icd11_data = json.load(f)

# Load full ICD-10 data from CSV
import pandas as pd
icd10_df = pd.read_csv('data/icd10_full.csv')
icd10_data = icd10_df.to_dict('records')

def detect_icd_version(code):
    if re.match(r'^[A-Z]\d{2,3}(\.\d+)?$', code):
        return "ICD-10"
    if re.match(r'^\d*[A-Z]\d{2}', code) and not re.match(r'^[A-Z]\d{2,3}(\.\d+)?$', code):
        return "ICD-11"
    return "Unknown"

@app.get("/api/v1/search/unified")
def unified_search(query: str = Query(..., min_length=2), limit: int = 20):
    results = []
    query_lower = query.lower()
    
    # Search ICD-10
    for code in icd10_data:
        if query_lower in str(code['term']).lower() or query_lower in str(code['code']).lower():
            results.append({
                "code": code['code'],
                "title": code['term'],
                "chapter": code['chapter'],
                "version": "ICD-10",
                "confidence": 0.9
            })
    
    # Search ICD-11
    for code in icd11_data:
        if query_lower in code['title'].lower() or query_lower in code['code'].lower():
            results.append({
                "code": code['code'],
                "title": code['title'],
                "chapter": code['chapter'],
                "version": "ICD-11",
                "confidence": 0.9
            })
    
    return {
        "query": query,
        "total_results": len(results[:limit]),
        "results": results[:limit]
    }

@app.get("/api/v1/code/{code}")
def get_any_code(code: str):
    version = detect_icd_version(code)
    
    if version == "ICD-10":
        for item in icd10_data:
            if str(item['code']) == code:
                return {
                    "code": item['code'],
                    "title": item['term'],
                    "chapter": item['chapter'],
                    "version": "ICD-10"
                }
    
    elif version == "ICD-11":
        for item in icd11_data:
            if item['code'] == code:
                return {**item, "version": "ICD-11"}
    
    return {"error": "Code not found", "searched_version": version}