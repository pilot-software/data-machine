"""
Drug Database Endpoints
"""
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List
from pydantic import BaseModel, Field
from sqlalchemy import text
from app.db.database import SessionLocal
from app.services.search_logger import search_logger
from app.middleware.auth import verify_api_key
import time

router = APIRouter(prefix="/api/v1/drugs", tags=["drugs"], dependencies=[Depends(verify_api_key)])

@router.get("/search")
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

@router.get("/{drug_id}")
async def get_drug_details(drug_id: int):
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

@router.post("/interactions")
async def check_drug_interactions(req: InteractionRequest):
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
