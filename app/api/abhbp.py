"""Ayushman Bharat HBP API Endpoints"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from app.db.database import get_db
from app.db.models import ABHBPProcedure

router = APIRouter(prefix="/api/v1/abhbp", tags=["Ayushman Bharat HBP"])


@router.get("/search")
async def search_procedures(
    q: str = Query(..., min_length=2),
    specialty: Optional[str] = None,
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    """Search AB-HBP procedures by name, code, or specialty"""
    
    query = db.query(ABHBPProcedure).filter(ABHBPProcedure.active == True)
    
    if specialty:
        query = query.filter(ABHBPProcedure.specialty.ilike(f"%{specialty}%"))
    
    results = query.filter(
        or_(
            ABHBPProcedure.package_code.ilike(f"%{q}%"),
            ABHBPProcedure.package_name.ilike(f"%{q}%"),
            func.to_tsvector('english', ABHBPProcedure.package_name).match(q)
        )
    ).limit(limit).all()
    
    return {
        "count": len(results),
        "results": [
            {
                "package_code": p.package_code,
                "package_name": p.package_name,
                "specialty": p.specialty,
                "base_rate": float(p.base_rate) if p.base_rate else None,
                "procedure_type": p.procedure_type,
                "preauth_required": p.preauth_required
            }
            for p in results
        ]
    }


@router.get("/{package_code}")
async def get_procedure(package_code: str, db: Session = Depends(get_db)):
    """Get procedure details by package code"""
    
    procedure = db.query(ABHBPProcedure).filter(
        ABHBPProcedure.package_code == package_code,
        ABHBPProcedure.active == True
    ).first()
    
    if not procedure:
        raise HTTPException(status_code=404, detail="Package not found")
    
    return {
        "package_code": procedure.package_code,
        "package_name": procedure.package_name,
        "specialty": procedure.specialty,
        "procedure_type": procedure.procedure_type,
        "base_rate": float(procedure.base_rate) if procedure.base_rate else None,
        "icd10_codes": procedure.icd10_codes,
        "empanelment_required": procedure.empanelment_required,
        "preauth_required": procedure.preauth_required,
        "hbp_category": procedure.hbp_category
    }


@router.get("/specialties/list")
async def list_specialties(db: Session = Depends(get_db)):
    """Get all available specialties"""
    
    specialties = db.query(ABHBPProcedure.specialty).filter(
        ABHBPProcedure.active == True,
        ABHBPProcedure.specialty.isnot(None)
    ).distinct().all()
    
    return {"specialties": sorted([s[0] for s in specialties if s[0]])}
