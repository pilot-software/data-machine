"""
SNOMED CT Drug API Endpoints
Production-grade endpoints for 89K+ Indian drugs with SNOMED codes
"""

from fastapi import APIRouter, Query, HTTPException, Depends, Path
from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import text, func
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.search_logger import search_logger
from app.middleware.auth import verify_api_key
from functools import lru_cache
import time

router = APIRouter(
    prefix="/api/v1/snomed",
    tags=["snomed-drugs"],
    dependencies=[Depends(verify_api_key)]
)

# ============================================================================
# Response Models
# ============================================================================

class SnomedBrandResponse(BaseModel):
    snomed_id: int
    brand_name: str
    generic_name: Optional[str]
    generic_snomed_id: Optional[int]
    product_name: Optional[str]
    supplier_name: Optional[str]
    manufacturer_country: Optional[str]
    license_status: Optional[str]
    indication: Optional[str]
    therapeutic_role: Optional[str]
    active: bool

class SnomedGenericResponse(BaseModel):
    snomed_id: int
    generic_name: str
    indication: Optional[str]
    contra_indication: Optional[str]
    therapeutic_role: Optional[str]
    dose_form: Optional[str]
    drug_classification: Optional[str]
    brand_count: int

class SnomedAlternativeResponse(BaseModel):
    snomed_id: int
    brand_name: str
    supplier_name: Optional[str]
    license_status: Optional[str]
    same_generic: bool

class SnomedSupplierResponse(BaseModel):
    snomed_id: int
    supplier_name: str
    country: Optional[str]
    drug_count: int
    active: bool

class SearchResponse(BaseModel):
    query: str
    total: int
    page: int
    page_size: int
    response_time_ms: float
    results: List[SnomedBrandResponse]

# ============================================================================
# Endpoints
# ============================================================================

@router.get("/search", response_model=SearchResponse)
async def search_snomed_drugs(
    q: str = Query(..., min_length=2, description="Search query (brand, generic, indication)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    filter_active: bool = Query(True, description="Filter active drugs only"),
    db: Session = Depends(get_db)
):
    """
    Search SNOMED drugs by brand name, generic name, or indication
    
    - **89,447 Indian brands** with SNOMED codes
    - Full-text search with relevance ranking
    - Includes manufacturer and generic information
    """
    start_time = time.time()
    
    try:
        # Build search query with relevance ranking
        sql = text("""
            SELECT 
                brand_snomed_id as snomed_id,
                brand_name,
                generic_name,
                generic_snomed_id,
                product_name,
                supplier_name,
                manufacturer_country,
                license_status,
                indication,
                therapeutic_role,
                active,
                CASE 
                    WHEN LOWER(brand_name) = LOWER(:q) THEN 1
                    WHEN LOWER(generic_name) = LOWER(:q) THEN 2
                    WHEN brand_name ILIKE :q_start THEN 3
                    WHEN generic_name ILIKE :q_start THEN 4
                    ELSE 5
                END as relevance
            FROM snomed_drugs_complete
            WHERE (
                brand_name ILIKE :q_like
                OR generic_name ILIKE :q_like
                OR indication ILIKE :q_like
                OR supplier_name ILIKE :q_like
            )
            AND (:filter_active = FALSE OR active = TRUE)
            ORDER BY relevance, brand_name
            LIMIT :limit OFFSET :offset
        """)
        
        offset = (page - 1) * page_size
        
        results = db.execute(sql, {
            "q": q,
            "q_start": f"{q}%",
            "q_like": f"%{q}%",
            "filter_active": filter_active,
            "limit": page_size,
            "offset": offset
        }).fetchall()
        
        # Get total count
        count_sql = text("""
            SELECT COUNT(*) 
            FROM snomed_drugs_complete
            WHERE (
                brand_name ILIKE :q_like
                OR generic_name ILIKE :q_like
                OR indication ILIKE :q_like
                OR supplier_name ILIKE :q_like
            )
            AND (:filter_active = FALSE OR active = TRUE)
        """)
        
        total = db.execute(count_sql, {
            "q_like": f"%{q}%",
            "filter_active": filter_active
        }).scalar()
        
        response_time = (time.time() - start_time) * 1000
        
        # Log search
        search_logger.log_search(q, len(results), response_time)
        
        return SearchResponse(
            query=q,
            total=total,
            page=page,
            page_size=page_size,
            response_time_ms=round(response_time, 2),
            results=[SnomedBrandResponse(**dict(r._mapping)) for r in results]
        )
        
    except Exception as e:
        raise HTTPException(500, f"Search failed: {str(e)}")


@router.get("/brands/{snomed_id}", response_model=SnomedBrandResponse)
async def get_brand_details(
    snomed_id: int = Path(..., description="SNOMED brand ID"),
    db: Session = Depends(get_db)
):
    """
    Get detailed information for a specific brand by SNOMED ID
    
    Returns complete drug information including:
    - Brand details
    - Generic formulation
    - Manufacturer
    - Indications and contraindications
    """
    try:
        sql = text("""
            SELECT 
                brand_snomed_id as snomed_id,
                brand_name,
                generic_name,
                generic_snomed_id,
                product_name,
                supplier_name,
                manufacturer_country,
                license_status,
                indication,
                therapeutic_role,
                active
            FROM snomed_drugs_complete
            WHERE brand_snomed_id = :snomed_id
        """)
        
        result = db.execute(sql, {"snomed_id": snomed_id}).fetchone()
        
        if not result:
            raise HTTPException(404, f"Brand with SNOMED ID {snomed_id} not found")
        
        return SnomedBrandResponse(**dict(result._mapping))
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch brand: {str(e)}")


@router.get("/generics/{snomed_id}", response_model=SnomedGenericResponse)
async def get_generic_details(
    snomed_id: int = Path(..., description="SNOMED generic ID"),
    db: Session = Depends(get_db)
):
    """
    Get generic drug details with brand count
    
    Returns:
    - Generic formulation details
    - Indications and contraindications
    - Number of available brands
    """
    try:
        sql = text("""
            SELECT 
                g.snomed_id,
                g.generic_name,
                g.indication,
                g.contra_indication,
                g.therapeutic_role,
                g.dose_form,
                g.drug_classification,
                COUNT(b.snomed_id) as brand_count
            FROM snomed_generics g
            LEFT JOIN snomed_brands b ON g.snomed_id = b.generic_id AND b.active = TRUE
            WHERE g.snomed_id = :snomed_id
            GROUP BY g.snomed_id, g.generic_name, g.indication, g.contra_indication,
                     g.therapeutic_role, g.dose_form, g.drug_classification
        """)
        
        result = db.execute(sql, {"snomed_id": snomed_id}).fetchone()
        
        if not result:
            raise HTTPException(404, f"Generic with SNOMED ID {snomed_id} not found")
        
        return SnomedGenericResponse(**dict(result._mapping))
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch generic: {str(e)}")


@router.get("/brands/{snomed_id}/alternatives", response_model=List[SnomedAlternativeResponse])
async def get_brand_alternatives(
    snomed_id: int = Path(..., description="SNOMED brand ID"),
    limit: int = Query(20, ge=1, le=100, description="Maximum alternatives to return"),
    db: Session = Depends(get_db)
):
    """
    Find alternative brands with the same generic formulation
    
    Use case: Find cheaper alternatives or substitutes
    Returns brands with the same active ingredient
    """
    try:
        # First get the generic_id of the requested brand
        brand_sql = text("""
            SELECT generic_id FROM snomed_brands WHERE snomed_id = :snomed_id
        """)
        
        brand_result = db.execute(brand_sql, {"snomed_id": snomed_id}).fetchone()
        
        if not brand_result or not brand_result.generic_id:
            raise HTTPException(404, "Brand not found or has no generic mapping")
        
        generic_id = brand_result.generic_id
        
        # Get all brands with same generic
        alternatives_sql = text("""
            SELECT 
                b.snomed_id,
                b.brand_name,
                s.supplier_name,
                b.license_status,
                TRUE as same_generic
            FROM snomed_brands b
            LEFT JOIN snomed_suppliers s ON b.supplier_id = s.snomed_id
            WHERE b.generic_id = :generic_id
            AND b.snomed_id != :snomed_id
            AND b.active = TRUE
            ORDER BY b.brand_name
            LIMIT :limit
        """)
        
        results = db.execute(alternatives_sql, {
            "generic_id": generic_id,
            "snomed_id": snomed_id,
            "limit": limit
        }).fetchall()
        
        return [SnomedAlternativeResponse(**dict(r._mapping)) for r in results]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch alternatives: {str(e)}")


@router.get("/generics/{snomed_id}/brands", response_model=List[SnomedBrandResponse])
async def get_brands_by_generic(
    snomed_id: int = Path(..., description="SNOMED generic ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get all brands for a specific generic formulation
    
    Returns paginated list of all brands containing this generic
    """
    try:
        offset = (page - 1) * page_size
        
        sql = text("""
            SELECT 
                brand_snomed_id as snomed_id,
                brand_name,
                generic_name,
                generic_snomed_id,
                product_name,
                supplier_name,
                manufacturer_country,
                license_status,
                indication,
                therapeutic_role,
                active
            FROM snomed_drugs_complete
            WHERE generic_snomed_id = :snomed_id
            AND active = TRUE
            ORDER BY brand_name
            LIMIT :limit OFFSET :offset
        """)
        
        results = db.execute(sql, {
            "snomed_id": snomed_id,
            "limit": page_size,
            "offset": offset
        }).fetchall()
        
        return [SnomedBrandResponse(**dict(r._mapping)) for r in results]
        
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch brands: {str(e)}")


@router.get("/suppliers/{snomed_id}", response_model=SnomedSupplierResponse)
async def get_supplier_details(
    snomed_id: int = Path(..., description="SNOMED supplier ID"),
    db: Session = Depends(get_db)
):
    """
    Get manufacturer/supplier details with drug count
    """
    try:
        sql = text("""
            SELECT 
                s.snomed_id,
                s.supplier_name,
                s.country,
                s.active,
                COUNT(b.snomed_id) as drug_count
            FROM snomed_suppliers s
            LEFT JOIN snomed_brands b ON s.snomed_id = b.supplier_id AND b.active = TRUE
            WHERE s.snomed_id = :snomed_id
            GROUP BY s.snomed_id, s.supplier_name, s.country, s.active
        """)
        
        result = db.execute(sql, {"snomed_id": snomed_id}).fetchone()
        
        if not result:
            raise HTTPException(404, f"Supplier with SNOMED ID {snomed_id} not found")
        
        return SnomedSupplierResponse(**dict(result._mapping))
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch supplier: {str(e)}")


@router.get("/suppliers/{snomed_id}/drugs", response_model=List[SnomedBrandResponse])
async def get_drugs_by_supplier(
    snomed_id: int = Path(..., description="SNOMED supplier ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get all drugs manufactured by a specific supplier
    """
    try:
        offset = (page - 1) * page_size
        
        sql = text("""
            SELECT 
                brand_snomed_id as snomed_id,
                brand_name,
                generic_name,
                generic_snomed_id,
                product_name,
                supplier_name,
                manufacturer_country,
                license_status,
                indication,
                therapeutic_role,
                active
            FROM snomed_drugs_complete
            WHERE supplier_name IN (
                SELECT supplier_name FROM snomed_suppliers WHERE snomed_id = :snomed_id
            )
            AND active = TRUE
            ORDER BY brand_name
            LIMIT :limit OFFSET :offset
        """)
        
        results = db.execute(sql, {
            "snomed_id": snomed_id,
            "limit": page_size,
            "offset": offset
        }).fetchall()
        
        return [SnomedBrandResponse(**dict(r._mapping)) for r in results]
        
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch drugs: {str(e)}")


@router.get("/autocomplete")
async def autocomplete_drugs(
    q: str = Query(..., min_length=2, max_length=50, description="Search prefix"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Fast autocomplete for drug search
    
    Returns top matching brand and generic names
    Optimized for typeahead/autocomplete UI
    """
    try:
        sql = text("""
            (
                SELECT DISTINCT brand_name as name, 'brand' as type
                FROM snomed_brands
                WHERE brand_name ILIKE :q_start
                AND active = TRUE
                LIMIT :limit
            )
            UNION ALL
            (
                SELECT DISTINCT generic_name as name, 'generic' as type
                FROM snomed_generics
                WHERE generic_name ILIKE :q_start
                LIMIT :limit
            )
            ORDER BY name
            LIMIT :limit
        """)
        
        results = db.execute(sql, {
            "q_start": f"{q}%",
            "limit": limit
        }).fetchall()
        
        return {
            "query": q,
            "suggestions": [{"name": r.name, "type": r.type} for r in results]
        }
        
    except Exception as e:
        raise HTTPException(500, f"Autocomplete failed: {str(e)}")


@router.get("/stats")
async def get_snomed_stats(db: Session = Depends(get_db)):
    """
    Get SNOMED database statistics
    
    Returns counts for all tables and last update time
    """
    try:
        stats_sql = text("""
            SELECT 
                (SELECT COUNT(*) FROM snomed_brands WHERE active = TRUE) as active_brands,
                (SELECT COUNT(*) FROM snomed_brands) as total_brands,
                (SELECT COUNT(*) FROM snomed_generics) as total_generics,
                (SELECT COUNT(*) FROM snomed_suppliers WHERE active = TRUE) as active_suppliers,
                (SELECT COUNT(*) FROM snomed_products) as total_products,
                (SELECT COUNT(*) FROM snomed_substances) as total_substances,
                (SELECT MAX(last_updated) FROM snomed_brands) as last_updated
        """)
        
        result = db.execute(stats_sql).fetchone()
        
        return {
            "active_brands": result.active_brands,
            "total_brands": result.total_brands,
            "total_generics": result.total_generics,
            "active_suppliers": result.active_suppliers,
            "total_products": result.total_products,
            "total_substances": result.total_substances,
            "last_updated": result.last_updated.isoformat() if result.last_updated else None,
            "coverage": "89,447 Indian brands with SNOMED CT codes"
        }
        
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch stats: {str(e)}")
