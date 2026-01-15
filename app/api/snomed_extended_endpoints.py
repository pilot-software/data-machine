"""
Extended SNOMED API - Drug Hierarchies, Classifications, Dosages
"""

from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from sqlalchemy import text
from app.db.database import SessionLocal
from app.middleware.auth import verify_api_key

router = APIRouter(
    prefix="/api/v1/snomed/extended",
    tags=["snomed-extended"],
    dependencies=[Depends(verify_api_key)]
)

@router.get("/drug-classes")
async def get_drug_classes():
    """Get available drug classifications"""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT 
                COUNT(*) FILTER (WHERE is_antibiotic) as antibiotics,
                COUNT(*) FILTER (WHERE is_analgesic) as analgesics,
                COUNT(*) FILTER (WHERE is_antihypertensive) as antihypertensives,
                COUNT(*) FILTER (WHERE is_antidiabetic) as antidiabetics,
                COUNT(*) FILTER (WHERE is_antiinflammatory) as antiinflammatories
            FROM snomed_drug_classes
        """)).fetchone()
        
        return {
            "drug_classes": {
                "antibiotics": result.antibiotics,
                "analgesics": result.analgesics,
                "antihypertensives": result.antihypertensives,
                "antidiabetics": result.antidiabetics,
                "antiinflammatories": result.antiinflammatories
            }
        }
    finally:
        db.close()

@router.get("/antibiotics")
async def get_antibiotics(page: int = 1, page_size: int = 20):
    """Get all antibiotics"""
    db = SessionLocal()
    try:
        offset = (page - 1) * page_size
        
        results = db.execute(text("""
            SELECT b.snomed_id, b.brand_name, g.generic_name, s.supplier_name, c.drug_class
            FROM snomed_drug_classes c
            JOIN snomed_brands b ON c.drug_id = b.snomed_id
            LEFT JOIN snomed_generics g ON b.generic_id = g.snomed_id
            LEFT JOIN snomed_suppliers s ON b.supplier_id = s.snomed_id
            WHERE c.is_antibiotic = TRUE AND b.active = TRUE
            ORDER BY b.brand_name
            LIMIT :limit OFFSET :offset
        """), {"limit": page_size, "offset": offset}).fetchall()
        
        total = db.execute(text("""
            SELECT COUNT(*) FROM snomed_drug_classes WHERE is_antibiotic = TRUE
        """)).scalar()
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "antibiotics": [
                {
                    "snomed_id": r.snomed_id,
                    "brand_name": r.brand_name,
                    "generic_name": r.generic_name,
                    "supplier_name": r.supplier_name,
                    "drug_class": r.drug_class
                }
                for r in results
            ]
        }
    finally:
        db.close()

@router.get("/by-class/{drug_class}")
async def get_drugs_by_class(
    drug_class: str,
    page: int = 1,
    page_size: int = 20
):
    """Get drugs by classification (antibiotic, analgesic, etc.)"""
    db = SessionLocal()
    try:
        class_map = {
            "antibiotic": "is_antibiotic",
            "analgesic": "is_analgesic",
            "antihypertensive": "is_antihypertensive",
            "antidiabetic": "is_antidiabetic",
            "antiinflammatory": "is_antiinflammatory"
        }
        
        column = class_map.get(drug_class.lower())
        if not column:
            return {"error": "Invalid drug class"}
        
        offset = (page - 1) * page_size
        
        results = db.execute(text(f"""
            SELECT b.snomed_id, b.brand_name, g.generic_name, s.supplier_name
            FROM snomed_drug_classes c
            JOIN snomed_brands b ON c.drug_id = b.snomed_id
            LEFT JOIN snomed_generics g ON b.generic_id = g.snomed_id
            LEFT JOIN snomed_suppliers s ON b.supplier_id = s.snomed_id
            WHERE c.{column} = TRUE AND b.active = TRUE
            ORDER BY b.brand_name
            LIMIT :limit OFFSET :offset
        """), {"limit": page_size, "offset": offset}).fetchall()
        
        return {
            "drug_class": drug_class,
            "page": page,
            "drugs": [
                {
                    "snomed_id": r.snomed_id,
                    "brand_name": r.brand_name,
                    "generic_name": r.generic_name,
                    "supplier_name": r.supplier_name
                }
                for r in results
            ]
        }
    finally:
        db.close()

@router.get("/definition/{snomed_id}")
async def get_drug_definition(snomed_id: int):
    """Get clinical definition for a drug"""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT d.definition, b.brand_name, g.generic_name
            FROM snomed_drug_definitions d
            JOIN snomed_brands b ON d.drug_id = b.snomed_id
            LEFT JOIN snomed_generics g ON b.generic_id = g.snomed_id
            WHERE d.drug_id = :snomed_id
        """), {"snomed_id": snomed_id}).fetchone()
        
        if not result:
            return {"error": "Definition not found"}
        
        return {
            "snomed_id": snomed_id,
            "brand_name": result.brand_name,
            "generic_name": result.generic_name,
            "definition": result.definition
        }
    finally:
        db.close()

@router.get("/dosage/{snomed_id}")
async def get_drug_dosage(snomed_id: int):
    """Get precise dosage information"""
    db = SessionLocal()
    try:
        results = db.execute(text("""
            SELECT attribute_type, value_numeric, value_text
            FROM snomed_drug_dosages
            WHERE drug_id = :snomed_id
        """), {"snomed_id": snomed_id}).fetchall()
        
        if not results:
            return {"error": "Dosage info not found"}
        
        dosage = {}
        for r in results:
            dosage[r.attribute_type] = r.value_numeric or r.value_text
        
        return {
            "snomed_id": snomed_id,
            "dosage_info": dosage
        }
    finally:
        db.close()

@router.get("/hierarchy/{snomed_id}")
async def get_drug_hierarchy(snomed_id: int):
    """Get drug hierarchy (parent classes)"""
    db = SessionLocal()
    try:
        results = db.execute(text("""
            WITH RECURSIVE hierarchy AS (
                SELECT drug_id, parent_id, 1 as level
                FROM snomed_drug_hierarchy
                WHERE drug_id = :snomed_id
                
                UNION ALL
                
                SELECT h.drug_id, h.parent_id, hierarchy.level + 1
                FROM snomed_drug_hierarchy h
                JOIN hierarchy ON h.drug_id = hierarchy.parent_id
                WHERE hierarchy.level < 10
            )
            SELECT DISTINCT parent_id, level
            FROM hierarchy
            ORDER BY level
        """), {"snomed_id": snomed_id}).fetchall()
        
        return {
            "snomed_id": snomed_id,
            "hierarchy": [
                {"parent_id": r.parent_id, "level": r.level}
                for r in results
            ]
        }
    finally:
        db.close()
