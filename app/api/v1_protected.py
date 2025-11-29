"""
Protected API endpoints (with auth)
"""
from fastapi import APIRouter, Depends
from app.middleware.auth import verify_api_key

router = APIRouter(prefix="/api/v1/protected", tags=["protected"], dependencies=[Depends(verify_api_key)])

@router.get("/stats")
async def get_stats():
    """Get database statistics (protected)"""
    from app.db.database import SessionLocal
    from sqlalchemy import text
    
    db = SessionLocal()
    try:
        stats = {}
        
        # ICD codes
        icd10 = db.execute(text("SELECT COUNT(*) FROM icd10_codes")).scalar()
        icd11 = db.execute(text("SELECT COUNT(*) FROM icd11_codes")).scalar()
        
        # Drugs
        generics = db.execute(text("SELECT COUNT(*) FROM generic_ingredients")).scalar()
        brands = db.execute(text("SELECT COUNT(*) FROM indian_brand_drugs")).scalar()
        
        # Procedures
        abhbp = db.execute(text("SELECT COUNT(*) FROM abhbp_procedures")).scalar()
        
        return {
            "icd10_codes": icd10,
            "icd11_codes": icd11,
            "generic_drugs": generics,
            "brand_drugs": brands,
            "abhbp_procedures": abhbp,
            "total_records": icd10 + icd11 + generics + brands + abhbp
        }
    finally:
        db.close()

@router.get("/health/detailed")
async def detailed_health():
    """Detailed health check (protected)"""
    from app.db.database import SessionLocal
    from sqlalchemy import text
    import psutil
    
    db = SessionLocal()
    try:
        # Database check
        db.execute(text("SELECT 1"))
        db_status = "healthy"
        
        # System info
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        
        return {
            "status": "healthy",
            "database": db_status,
            "system": {
                "cpu_usage": f"{cpu}%",
                "memory_usage": f"{memory}%"
            }
        }
    except:
        return {"status": "unhealthy", "database": "error"}
    finally:
        db.close()
