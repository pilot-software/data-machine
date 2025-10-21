from fastapi import APIRouter, HTTPException, Query, Body, Depends
from typing import List, Optional
from pydantic import BaseModel, ValidationError
from app.core.service_factory import get_cache_service, get_repository
from app.services.terminology_service import TerminologyService

def get_terminology_service():
    cache_service = get_cache_service()
    repository = get_repository()
    return TerminologyService(cache_service, repository)
from app.models.validation import SearchRequest, ClinicalQuery
from app.core.exceptions import handle_database_error, handle_validation_error, handle_service_error
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/enterprise", tags=["enterprise"])


@router.get("/search/icd10/advanced")
async def advanced_icd10_search(
    query: str = Query(..., min_length=2, max_length=100, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    chapter: Optional[str] = Query(None, max_length=20, description="Filter by ICD-10 chapter"),
    include_inactive: bool = Query(False, description="Include inactive codes"),
    fuzzy_threshold: float = Query(0.3, ge=0.1, le=1.0, description="Fuzzy match threshold")
):
    """Advanced ICD-10 search with multiple algorithms and filters"""
    try:
        # Validate and sanitize input
        search_req = SearchRequest(query=query, limit=limit, chapter=chapter)
        
        terminology_service = get_terminology_service()
        result = await terminology_service.advanced_search(
            query=search_req.query,
            limit=search_req.limit,
            chapter_filter=search_req.chapter,
            include_inactive=include_inactive,
            fuzzy_threshold=fuzzy_threshold
        )
        return result
        
    except ValidationError as e:
        handle_validation_error(e)
    except Exception as e:
        handle_database_error(e, "advanced ICD-10 search")


@router.get("/icd10/{code}/hierarchy")
async def get_icd10_hierarchy(code: str):
    """Get ICD-10 code with hierarchical context (parents, children, siblings)"""
    try:
        from app.models.validation import CodeRequest
        code_req = CodeRequest(code=code)
        terminology_service = get_terminology_service()
        result = await terminology_service.get_code_details(code_req.code)
        
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hierarchy lookup error: {e}")
        raise HTTPException(status_code=500, detail="Hierarchy service error")


@router.post("/clinical/decision-support")
async def clinical_decision_support(query: ClinicalQuery):
    """Clinical decision support based on symptoms and patient context"""
    try:
        # Input is already validated by Pydantic model
        terminology_service = get_terminology_service()
        result = await terminology_service.clinical_analysis(query.symptoms)
        
        if 'error' in result:
            handle_service_error(Exception(result['error']), "Clinical decision support")
        
        # Add patient context if provided
        if query.patient_age or query.patient_gender:
            result['patient_context'] = {
                'age': query.patient_age,
                'gender': query.patient_gender
            }
        
        return result
        
    except ValidationError as e:
        handle_validation_error(e)
    except HTTPException:
        raise
    except Exception as e:
        handle_service_error(e, "Clinical decision support")


@router.get("/analytics/search-stats")
async def get_search_analytics():
    """Get search analytics and performance metrics"""
    try:
        from app.services.redis_service import redis_service
        
        # Basic cache info (redis_service.get_stats() doesn't exist, so use basic info)
        cache_info = {
            'redis_connected': redis_service.redis_client is not None,
            'cache_enabled': True
        }
        
        return {
            'cache_stats': cache_info,
            'service_status': 'operational',
            'features': {
                'advanced_search': True,
                'hierarchy_navigation': True,
                'clinical_decision_support': True,
                'fuzzy_matching': True,
                'multi_algorithm_search': True
            }
        }
        
    except Exception as e:
        handle_service_error(e, "Analytics service")


@router.get("/chapters")
async def get_icd10_chapters():
    """Get all ICD-10 chapters for filtering"""
    chapters = [
        {"code": "A-B", "name": "Certain infectious and parasitic diseases"},
        {"code": "C-D", "name": "Neoplasms"},
        {"code": "D", "name": "Diseases of the blood and blood-forming organs"},
        {"code": "E", "name": "Endocrine, nutritional and metabolic diseases"},
        {"code": "F", "name": "Mental, Behavioral and Neurodevelopmental disorders"},
        {"code": "G", "name": "Diseases of the nervous system"},
        {"code": "H", "name": "Diseases of the eye and ear"},
        {"code": "I", "name": "Diseases of the circulatory system"},
        {"code": "J", "name": "Diseases of the respiratory system"},
        {"code": "K", "name": "Diseases of the digestive system"},
        {"code": "L", "name": "Diseases of the skin and subcutaneous tissue"},
        {"code": "M", "name": "Diseases of the musculoskeletal system"},
        {"code": "N", "name": "Diseases of the genitourinary system"},
        {"code": "O", "name": "Pregnancy, childbirth and the puerperium"},
        {"code": "P", "name": "Certain conditions originating in the perinatal period"},
        {"code": "Q", "name": "Congenital malformations and chromosomal abnormalities"},
        {"code": "R", "name": "Symptoms, signs and abnormal findings"},
        {"code": "S-T", "name": "Injury, poisoning and external causes"},
        {"code": "V-Y", "name": "External causes of morbidity"},
        {"code": "Z", "name": "Factors influencing health status"}
    ]
    
    return {"chapters": chapters}