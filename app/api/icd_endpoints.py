"""
ICD-10/11 Code Endpoints
"""
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional
from sqlalchemy import text
from app.db.database import SessionLocal
from app.services.search_logger import search_logger
from app.middleware.auth import verify_api_key
import time

router = APIRouter(prefix="/api/v1/icd", tags=["icd"], dependencies=[Depends(verify_api_key)])

@router.get("/search")
async def search_icd_codes(
    q: str = Query(..., min_length=2, description="Search query"),
    systems: str = Query("icd10,icd11", description="Comma-separated: icd10,icd11"),
    chapter: Optional[str] = Query(None, description="Filter by chapter"),
    fuzzy: float = Query(0.3, ge=0.1, le=1.0, description="Fuzzy threshold"),
    autocomplete: bool = Query(False, description="Autocomplete mode"),
    limit: int = Query(10, ge=1, le=50)
):
    """Unified ICD-10/11 search"""
    start = time.time()
    db = SessionLocal()
    results = {"icd10": [], "icd11": []}
    
    try:
        systems_list = [s.strip() for s in systems.split(",")]
        
        if "icd10" in systems_list:
            sql = text("""
                SELECT code, term, short_desc, chapter,
                    CASE 
                        WHEN LOWER(code) = LOWER(:q) THEN 1
                        WHEN LOWER(term) LIKE LOWER(:q_start) THEN 2
                        WHEN term ILIKE :q_like THEN 3
                        ELSE 4
                    END as relevance
                FROM icd10_codes
                WHERE (code ILIKE :q_like OR term ILIKE :q_like)
                    AND active = true
                    AND (:chapter IS NULL OR chapter ILIKE :chapter_like)
                ORDER BY relevance, code
                LIMIT :limit
            """)
            rows = db.execute(sql, {
                "q": q, "q_start": f"{q}%", "q_like": f"%{q}%",
                "chapter": chapter, "chapter_like": f"%{chapter}%" if chapter else None,
                "limit": limit
            }).fetchall()
            results["icd10"] = [dict(r._mapping) for r in rows]
        
        if "icd11" in systems_list:
            sql = text("""
                SELECT code, title as term, definition, chapter
                FROM icd11_codes
                WHERE (code ILIKE :q_like OR title ILIKE :q_like)
                ORDER BY code
                LIMIT :limit
            """)
            rows = db.execute(sql, {"q_like": f"%{q}%", "limit": limit}).fetchall()
            results["icd11"] = [dict(r._mapping) for r in rows]
        
        response_time = (time.time() - start) * 1000
        search_logger.log_search(q, len(results["icd10"]) + len(results["icd11"]), response_time)
        
        return {
            "query": q,
            "systems": systems_list,
            "autocomplete_mode": autocomplete,
            "results": results,
            "total": len(results["icd10"]) + len(results["icd11"]),
            "response_time_ms": round(response_time, 2)
        }
    finally:
        db.close()

@router.get("/chapters")
async def get_chapters():
    """List all ICD-10 chapters"""
    return {
        "chapters": [
            {"code": "A-B", "name": "Infectious and parasitic diseases"},
            {"code": "C-D", "name": "Neoplasms"},
            {"code": "E", "name": "Endocrine, nutritional and metabolic"},
            {"code": "F", "name": "Mental and behavioral disorders"},
            {"code": "G", "name": "Nervous system"},
            {"code": "H", "name": "Eye, ear, and related"},
            {"code": "I", "name": "Circulatory system"},
            {"code": "J", "name": "Respiratory system"},
            {"code": "K", "name": "Digestive system"},
            {"code": "L", "name": "Skin and subcutaneous tissue"},
            {"code": "M", "name": "Musculoskeletal system"},
            {"code": "N", "name": "Genitourinary system"},
            {"code": "O", "name": "Pregnancy and childbirth"},
            {"code": "P", "name": "Perinatal conditions"},
            {"code": "Q", "name": "Congenital malformations"},
            {"code": "R", "name": "Symptoms and signs"},
            {"code": "S-T", "name": "Injury and poisoning"},
            {"code": "V-Y", "name": "External causes"},
            {"code": "Z", "name": "Health status factors"}
        ]
    }

@router.get("/{code}")
async def get_code_details(
    code: str,
    hierarchy: bool = Query(False, description="Include parent/children")
):
    """Get ICD code details with optional hierarchy"""
    db = SessionLocal()
    try:
        sql = text("SELECT * FROM icd10_codes WHERE code = :code")
        result = db.execute(sql, {"code": code}).fetchone()
        
        if not result:
            raise HTTPException(404, "Code not found")
        
        data = dict(result._mapping)
        
        if hierarchy:
            parent_sql = text("SELECT * FROM icd10_codes WHERE code = :parent")
            children_sql = text("SELECT * FROM icd10_codes WHERE parent_code = :code LIMIT 20")
            
            parent = db.execute(parent_sql, {"parent": data.get("parent_code")}).fetchone()
            children = db.execute(children_sql, {"code": code}).fetchall()
            
            data["parent"] = dict(parent._mapping) if parent else None
            data["children"] = [dict(c._mapping) for c in children]
        
        return data
    finally:
        db.close()
