"""
Ayushman Bharat HBP Endpoints
"""
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import ABHBPProcedure
from app.middleware.auth import verify_api_key

router = APIRouter(prefix="/api/v1/abhbp", tags=["abhbp"], dependencies=[Depends(verify_api_key)])

@router.get("/search")
async def search_procedures(
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

@router.get("/{package_code}")
async def get_procedure_details(package_code: str, db: Session = Depends(get_db)):
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
