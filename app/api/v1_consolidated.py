"""
Consolidated API v1 - Minimal, non-duplicate endpoints
"""
from fastapi import APIRouter, Query, HTTPException, Body, Depends
from typing import Optional, List
from pydantic import BaseModel, Field
from sqlalchemy import text, or_, func
from app.db.database import SessionLocal, get_db
from app.services.search_logger import search_logger
from app.db.models import ABHBPProcedure
from app.middleware.auth import verify_api_key
from sqlalchemy.orm import Session
import time

router = APIRouter(prefix="/api/v1", tags=["v1"], dependencies=[Depends(verify_api_key)])

# ============================================================================
# HEALTH ENDPOINTS
# ============================================================================

@router.get("/health")
async def health():
    """Basic health check"""
    return {"status": "healthy", "service": "HMS Terminology Service"}

@router.get("/health/detailed")
async def health_detailed():
    """Detailed health with DB/Redis status"""
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except:
        db_status = "unhealthy"
    finally:
        db.close()
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "redis": "not_configured"
    }

# ============================================================================
# ICD-10/11 UNIFIED SEARCH
# ============================================================================

@router.get("/icd10/search")
async def icd_search(
    q: str = Query(..., min_length=2, description="Search query"),
    systems: str = Query("icd10,icd11", description="Comma-separated: icd10,icd11"),
    chapter: Optional[str] = Query(None, description="Filter by chapter"),
    fuzzy: float = Query(0.3, ge=0.1, le=1.0, description="Fuzzy threshold"),
    autocomplete: bool = Query(False, description="Autocomplete mode"),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Unified ICD search - replaces 4 duplicate endpoints
    - Basic search, advanced search, unified search, autocomplete
    """
    start = time.time()
    db = SessionLocal()
    results = {"icd10": [], "icd11": []}
    
    try:
        systems_list = [s.strip() for s in systems.split(",")]
        
        # ICD-10 Search
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
        
        # ICD-11 Search
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

@router.get("/icd10/chapters")
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

@router.get("/icd10/{code}")
async def get_icd_code(
    code: str,
    hierarchy: bool = Query(False, description="Include parent/children")
):
    """Get ICD code details with optional hierarchy"""
    db = SessionLocal()
    try:
        # Get main code
        sql = text("SELECT * FROM icd10_codes WHERE code = :code")
        result = db.execute(sql, {"code": code}).fetchone()
        
        if not result:
            raise HTTPException(404, "Code not found")
        
        data = dict(result._mapping)
        
        # Add hierarchy if requested
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

# ============================================================================
# DRUG ENDPOINTS
# ============================================================================

@router.get("/drugs/search")
async def search_drugs(q: str = Query(..., min_length=2)):
    """Unified drug search: brand, generic, symptom"""
    start = time.time()
    db = SessionLocal()
    try:
        sql = text("""
            SELECT 
                ibd.brand_id, ibd.brand_name, ibd.manufacturer,
                gi.ingredient_name as generic_name, ibd.rxnorm_cui,
                gi.atc_code, ibd.strength, ibd.dosage_form,
                ibd.mrp, ibd.pack_size, gi.indications, gi.symptoms,
                CASE 
                    WHEN LOWER(ibd.brand_name) = LOWER(:q) THEN 1
                    WHEN LOWER(gi.ingredient_name) = LOWER(:q) THEN 2
                    ELSE 3
                END as relevance
            FROM indian_brand_drugs ibd
            JOIN generic_ingredients gi ON ibd.ingredient_id = gi.ingredient_id
            WHERE (ibd.brand_name ILIKE :q_like
                OR gi.ingredient_name ILIKE :q_like
                OR gi.indications ILIKE :q_like
                OR gi.symptoms ILIKE :q_like)
                AND ibd.active = true
            ORDER BY relevance, ibd.mrp
            LIMIT 50
        """)
        
        rows = db.execute(sql, {"q": q, "q_like": f"%{q}%"}).fetchall()
        drugs = [dict(r._mapping) for r in rows]
        
        response_time = (time.time() - start) * 1000
        search_logger.log_search(q, len(drugs), response_time)
        
        return {
            "query": q,
            "found": len(drugs) > 0,
            "total": len(drugs),
            "drugs": drugs,
            "response_time_ms": round(response_time, 2)
        }
    finally:
        db.close()

@router.get("/drugs/{drug_id}")
async def get_drug(drug_id: int):
    """Get drug details by ID"""
    db = SessionLocal()
    try:
        sql = text("""
            SELECT ibd.*, gi.ingredient_name, gi.indications, gi.symptoms
            FROM indian_brand_drugs ibd
            JOIN generic_ingredients gi ON ibd.ingredient_id = gi.ingredient_id
            WHERE ibd.brand_id = :id
        """)
        result = db.execute(sql, {"id": drug_id}).fetchone()
        
        if not result:
            raise HTTPException(404, "Drug not found")
        
        return dict(result._mapping)
    finally:
        db.close()

class InteractionRequest(BaseModel):
    drug_ids: List[int] = Field(..., min_items=2, max_items=10)

@router.post("/drugs/interactions")
async def check_interactions(req: InteractionRequest):
    """Check drug interactions"""
    db = SessionLocal()
    try:
        sql = text("""
            SELECT di.severity, di.description, di.clinical_effect,
                gi1.ingredient_name as drug_a, gi2.ingredient_name as drug_b
            FROM drug_interactions di
            JOIN generic_ingredients gi1 ON di.drug_a_id = gi1.ingredient_id
            JOIN generic_ingredients gi2 ON di.drug_b_id = gi2.ingredient_id
            WHERE di.drug_a_id IN (
                SELECT ingredient_id FROM indian_brand_drugs WHERE brand_id = ANY(:ids)
            )
            AND di.drug_b_id IN (
                SELECT ingredient_id FROM indian_brand_drugs WHERE brand_id = ANY(:ids)
            )
        """)
        
        rows = db.execute(sql, {"ids": req.drug_ids}).fetchall()
        interactions = [dict(r._mapping) for r in rows]
        
        return {
            "drug_ids": req.drug_ids,
            "has_interactions": len(interactions) > 0,
            "count": len(interactions),
            "interactions": interactions
        }
    finally:
        db.close()

# ============================================================================
# AYUSHMAN BHARAT HBP
# ============================================================================

@router.get("/abhbp/search")
async def search_abhbp(
    q: str = Query(..., min_length=2),
    specialty: Optional[str] = None,
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    """Search AB-HBP procedures"""
    query = db.query(ABHBPProcedure).filter(ABHBPProcedure.active == True)
    
    if specialty:
        query = query.filter(ABHBPProcedure.specialty.ilike(f"%{specialty}%"))
    
    results = query.filter(
        or_(
            ABHBPProcedure.package_code.ilike(f"%{q}%"),
            ABHBPProcedure.package_name.ilike(f"%{q}%")
        )
    ).limit(limit).all()
    
    return {
        "query": q,
        "count": len(results),
        "results": [
            {
                "package_code": p.package_code,
                "package_name": p.package_name,
                "specialty": p.specialty,
                "base_rate": float(p.base_rate) if p.base_rate else None,
                "procedure_type": p.procedure_type
            }
            for p in results
        ]
    }

@router.get("/abhbp/{package_code}")
async def get_abhbp(package_code: str, db: Session = Depends(get_db)):
    """Get AB-HBP procedure details"""
    proc = db.query(ABHBPProcedure).filter(
        ABHBPProcedure.package_code == package_code,
        ABHBPProcedure.active == True
    ).first()
    
    if not proc:
        raise HTTPException(404, "Package not found")
    
    return {
        "package_code": proc.package_code,
        "package_name": proc.package_name,
        "specialty": proc.specialty,
        "procedure_type": proc.procedure_type,
        "base_rate": float(proc.base_rate) if proc.base_rate else None,
        "icd10_codes": proc.icd10_codes,
        "preauth_required": proc.preauth_required
    }
