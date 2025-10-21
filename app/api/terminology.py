from fastapi import APIRouter, HTTPException, Query
from typing import List
import time
import logging
from pydantic import ValidationError
from app.models.terminology import (
    AutocompleteRequest, 
    AutocompleteResponse
)
from app.services.health_service import health_service
from app.core.service_factory import get_cache_service, get_repository
from app.services.terminology_service import TerminologyService
from app.models.validation import SearchRequest
from app.core.exceptions import handle_validation_error, handle_service_error


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["terminology"])


@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "service": "HMS Terminology Service"}

@router.get("/health/detailed")
async def detailed_health_check():
    """Comprehensive health check with dependency status"""
    try:
        health_status = await health_service.get_comprehensive_health()
        
        # Return appropriate HTTP status based on health
        if health_status["status"] == "unhealthy":
            raise HTTPException(status_code=503, detail=health_status)
        elif health_status["status"] == "degraded":
            raise HTTPException(status_code=200, detail=health_status)  # Still return 200 for degraded
        
        return health_status
        
    except HTTPException:
        raise
    except Exception as e:
        handle_service_error(e, "Health check service")

@router.get("/health/database")
async def database_health():
    """Database-specific health check"""
    try:
        db_health = await health_service.check_database()
        if db_health["status"] != "healthy":
            raise HTTPException(status_code=503, detail=db_health)
        return db_health
    except HTTPException:
        raise
    except Exception as e:
        handle_service_error(e, "Database health check")

@router.get("/health/redis")
async def redis_health():
    """Redis-specific health check"""
    try:
        redis_health = await health_service.check_redis()
        if redis_health["status"] != "healthy":
            raise HTTPException(status_code=503, detail=redis_health)
        return redis_health
    except HTTPException:
        raise
    except Exception as e:
        handle_service_error(e, "Redis health check")





@router.get("/search/unified")
async def unified_search(
    query: str = Query(..., min_length=2, max_length=100, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results")
):
    """Unified search across ICD-10 and ICD-11"""
    try:
        # Validate input
        search_req = SearchRequest(query=query, limit=limit)
        
        # Get services via dependency injection
        cache_service = get_cache_service()
        repository = get_repository()
        terminology_service = TerminologyService(cache_service, repository)
        
        # Use dedicated unified search method
        result = await terminology_service.unified_search(
            query=search_req.query,
            limit=search_req.limit
        )
        
        return result
        
    except ValidationError as e:
        handle_validation_error(e)
    except Exception as e:
        handle_service_error(e, "Unified search")

@router.get("/autocomplete/loinc")
async def autocomplete_loinc(
    query: str = Query(..., min_length=2, max_length=100, description="Search query for LOINC codes"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of suggestions")
):
    """Autocomplete LOINC codes - placeholder for future implementation"""
    try:
        # Validate input
        search_req = SearchRequest(query=query, limit=limit)
        
        start_time = time.time()
        
        # TODO: Implement LOINC search from local database
        suggestions = [
            {
                "code": "33747-0",
                "component": "Hemoglobin A1c",
                "system": "Blood",
                "unit": "%"
            }
        ]
        
        query_time_ms = (time.time() - start_time) * 1000
        
        return {
            "suggestions": suggestions,
            "total_count": len(suggestions),
            "query_time_ms": round(query_time_ms, 2)
        }
        
    except ValidationError as e:
        handle_validation_error(e)
    except Exception as e:
        handle_service_error(e, "LOINC autocomplete")





