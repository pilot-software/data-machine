"""
Minimal Drug API - ONE unified endpoint
"""

from fastapi import APIRouter, Query
from sqlalchemy import text
from app.db.database import SessionLocal

router = APIRouter(prefix="/api/v1/drugs", tags=["drugs"])


@router.get("/search")
async def search_drugs(q: str = Query(..., min_length=2)):
    """
    ONE endpoint for everything: brand, generic, symptom search
    Returns complete data in single response
    """
    db = SessionLocal()
    try:
        # Simple unified query
        sql = text("""
            SELECT 
                ibd.brand_id,
                ibd.brand_name,
                ibd.manufacturer,
                gi.ingredient_name as generic_name,
                ibd.rxnorm_cui,
                gi.atc_code,
                ibd.strength,
                ibd.dosage_form,
                ibd.route,
                ibd.mrp,
                ibd.pack_size,
                ibd.prescription_required,
                gi.indications,
                gi.symptoms,
                gi.therapeutic_class,
                CASE 
                    WHEN LOWER(ibd.brand_name) = LOWER(:query) THEN 1
                    WHEN LOWER(gi.ingredient_name) = LOWER(:query) THEN 2
                    WHEN ibd.brand_name ILIKE :query_like THEN 3
                    WHEN gi.ingredient_name ILIKE :query_like THEN 4
                    ELSE 5
                END as relevance
            FROM indian_brand_drugs ibd
            JOIN generic_ingredients gi ON ibd.ingredient_id = gi.ingredient_id
            WHERE 
                (ibd.brand_name ILIKE :query_like
                OR gi.ingredient_name ILIKE :query_like
                OR gi.indications ILIKE :query_like
                OR gi.symptoms ILIKE :query_like
                OR gi.conditions ILIKE :query_like)
                AND ibd.active = true
            ORDER BY relevance, ibd.mrp ASC
            LIMIT 50
        """)
        
        results = db.execute(sql, {
            "query": q,
            "query_like": f"%{q}%"
        }).fetchall()
        
        if not results:
            return {
                "query": q,
                "found": False,
                "message": "No drugs found",
                "drugs": []
            }
        
        # Convert to list of dicts
        drugs = [dict(r._mapping) for r in results]
        
        # Check if exact generic match
        is_exact_generic = any(d['generic_name'].lower() == q.lower() for d in drugs)
        
        response = {
            "query": q,
            "found": True,
            "search_type": "generic" if is_exact_generic else "fuzzy",
            "total_results": len(drugs),
            "drugs": drugs
        }
        
        # Add generic info if exact match
        if is_exact_generic:
            first_drug = drugs[0]
            response["generic_info"] = {
                "name": first_drug['generic_name'],
                "rxnorm_cui": first_drug['rxnorm_cui'],
                "indications": first_drug['indications'],
                "symptoms": first_drug['symptoms'],
                "total_brands": len(drugs)
            }
        
        return response
        
    finally:
        db.close()


@router.get("/quick/{drug_id}")
async def get_drug_quick(drug_id: int):
    """Quick lookup by brand_id"""
    db = SessionLocal()
    try:
        sql = text("""
            SELECT 
                ibd.*,
                gi.ingredient_name,
                gi.rxnorm_cui,
                gi.atc_code,
                gi.indications,
                gi.symptoms,
                gi.therapeutic_class
            FROM indian_brand_drugs ibd
            JOIN generic_ingredients gi ON ibd.ingredient_id = gi.ingredient_id
            WHERE ibd.brand_id = :drug_id
        """)
        
        result = db.execute(sql, {"drug_id": drug_id}).fetchone()
        return dict(result._mapping) if result else {"error": "Not found"}
        
    finally:
        db.close()


@router.post("/check-interaction")
async def check_interaction(drug_ids: list[int]):
    """Check interactions between multiple drugs"""
    db = SessionLocal()
    try:
        sql = text("""
            SELECT 
                di.severity,
                di.description,
                di.clinical_effect,
                gi1.ingredient_name as drug_a,
                gi2.ingredient_name as drug_b
            FROM drug_interactions di
            JOIN generic_ingredients gi1 ON di.drug_a_id = gi1.ingredient_id
            JOIN generic_ingredients gi2 ON di.drug_b_id = gi2.ingredient_id
            WHERE di.drug_a_id IN (
                SELECT ingredient_id FROM indian_brand_drugs WHERE brand_id = ANY(:drug_ids)
            )
            AND di.drug_b_id IN (
                SELECT ingredient_id FROM indian_brand_drugs WHERE brand_id = ANY(:drug_ids)
            )
        """)
        
        results = db.execute(sql, {"drug_ids": drug_ids}).fetchall()
        return {
            "has_interactions": len(results) > 0,
            "interactions": [dict(r._mapping) for r in results]
        }
        
    finally:
        db.close()
