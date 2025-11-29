"""
Clinical-friendly search API for doctors
"""
from fastapi import APIRouter, Query
from sqlalchemy import text
from app.db.database import SessionLocal
import time

router = APIRouter(prefix="/api/v1/clinical", tags=["clinical"])

# Common conditions mapping
COMMON_CONDITIONS = {
    "headache": {"codes": ["R51", "G43"], "urgency": "routine"},
    "fever": {"codes": ["R509"], "urgency": "urgent"},
    "diabetes": {"codes": ["E11", "E10"], "urgency": "chronic"},
    "hypertension": {"codes": ["I10"], "urgency": "chronic"}
}

@router.get("/search")
async def clinical_search(
    q: str = Query(..., min_length=2),
    limit: int = Query(5, le=10)
):
    """Doctor-friendly search with clinical context"""
    start = time.time()
    db = SessionLocal()
    
    try:
        # Check for typos/suggestions
        suggestions = []
        for condition in COMMON_CONDITIONS:
            if condition.startswith(q.lower()[:3]):
                suggestions.append(condition)
        
        # Search with clinical relevance
        sql = text("""
            SELECT 
                code,
                term as display,
                short_desc as description,
                chapter,
                CASE 
                    WHEN code IN ('R51', 'R509', 'E11', 'I10') THEN true
                    ELSE false
                END as is_common,
                CASE 
                    WHEN code LIKE 'R%' THEN 'routine'
                    WHEN code LIKE 'I%' THEN 'urgent'
                    ELSE 'routine'
                END as urgency,
                CASE 
                    WHEN LOWER(code) = LOWER(:q) THEN 1
                    WHEN LOWER(term) LIKE LOWER(:q_start) THEN 2
                    ELSE 3
                END as relevance
            FROM icd10_codes
            WHERE (code ILIKE :q_like OR term ILIKE :q_like)
                AND active = true
            ORDER BY is_common DESC, relevance, code
            LIMIT :limit
        """)
        
        rows = db.execute(sql, {
            "q": q,
            "q_start": f"{q}%",
            "q_like": f"%{q}%",
            "limit": limit
        }).fetchall()
        
        results = []
        for r in rows:
            result = dict(r._mapping)
            
            # Add clinical hints
            if "headache" in result["display"].lower():
                result["typical_symptoms"] = "Pain, pressure, throbbing"
                result["red_flags"] = ["sudden severe", "with fever", "after trauma"]
            elif "fever" in result["display"].lower():
                result["typical_symptoms"] = "Elevated temperature >38°C"
                result["red_flags"] = ["persistent >3 days", "with rash", "in infant"]
            
            results.append(result)
        
        response_time = (time.time() - start) * 1000
        
        return {
            "query": q,
            "did_you_mean": suggestions[0] if suggestions else None,
            "total": len(results),
            "results": results,
            "response_time_ms": round(response_time, 2)
        }
        
    finally:
        db.close()

@router.get("/common")
async def get_common_conditions():
    """Get most common conditions for quick access"""
    return {
        "categories": [
            {
                "name": "Symptoms",
                "conditions": [
                    {"code": "R51", "name": "Headache", "icon": "🤕"},
                    {"code": "R509", "name": "Fever", "icon": "🌡️"},
                    {"code": "R05", "name": "Cough", "icon": "😷"}
                ]
            },
            {
                "name": "Chronic",
                "conditions": [
                    {"code": "E11", "name": "Type 2 Diabetes", "icon": "💉"},
                    {"code": "I10", "name": "Hypertension", "icon": "❤️"}
                ]
            }
        ]
    }
