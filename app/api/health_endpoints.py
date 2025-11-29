"""
Health Check Endpoints
"""
from fastapi import APIRouter
from sqlalchemy import text
from app.db.database import SessionLocal

router = APIRouter(prefix="/api/v1", tags=["health"])

@router.get("/health")
async def health_check():
    """Basic health check (no auth required)"""
    return {"status": "healthy", "service": "Medical Library API"}

@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health with DB status (no auth required)"""
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
