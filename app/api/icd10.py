from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import ValidationError
from app.models.validation import SearchRequest, CodeRequest
from app.core.exceptions import handle_database_error, handle_validation_error, handle_service_error
from app.core.service_factory import get_cache_service, get_repository
from app.services.terminology_service import TerminologyService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["icd10"])

@router.get("/autocomplete/icd10")
async def autocomplete_icd10(
    query: str = Query(..., min_length=2, max_length=100, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum suggestions")
):
    """ICD-10 autocomplete with validation"""
    try:
        # Validate and sanitize input
        search_req = SearchRequest(query=query, limit=limit)
        
        # Get service via DI
        cache_service = get_cache_service()
        repository = get_repository()
        terminology_service = TerminologyService(cache_service, repository)
        
        # Use dedicated autocomplete service method
        result = await terminology_service.autocomplete_icd10(
            query=search_req.query,
            limit=search_req.limit
        )
        
        # Return autocomplete result directly
        return result
        
    except ValidationError as e:
        handle_validation_error(e)
    except Exception as e:
        handle_database_error(e, "ICD-10 autocomplete")

@router.get("/code/{code}")
async def get_icd10_code(code: str):
    """Get specific ICD-10 code details"""
    try:
        # Validate and sanitize code
        code_req = CodeRequest(code=code)
        
        # Get service via DI
        cache_service = get_cache_service()
        repository = get_repository()
        terminology_service = TerminologyService(cache_service, repository)
        
        # Get code details from service layer
        result = await terminology_service.get_code_details(code_req.code)
        
        if 'error' in result:
            raise HTTPException(status_code=404, detail="Code not found")
        
        return result
        
    except ValidationError as e:
        handle_validation_error(e)
    except HTTPException:
        raise
    except Exception as e:
        handle_database_error(e, "ICD-10 code lookup")

@router.get("/search/icd10")
async def search_icd10(
    query: str = Query(..., min_length=2, max_length=100, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    chapter: Optional[str] = Query(None, max_length=20, description="Chapter filter")
):
    """Basic ICD-10 search"""
    try:
        # Validate and sanitize input
        search_req = SearchRequest(query=query, limit=limit, chapter=chapter)
        
        # Get service via DI
        cache_service = get_cache_service()
        repository = get_repository()
        terminology_service = TerminologyService(cache_service, repository)
        
        result = await terminology_service.search_icd10(
            query=search_req.query,
            limit=search_req.limit,
            chapter_filter=search_req.chapter
        )
        
        return result
        
    except ValidationError as e:
        handle_validation_error(e)
    except Exception as e:
        handle_database_error(e, "ICD-10 search")