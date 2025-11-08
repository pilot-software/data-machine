from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from rapidfuzz import fuzz
from app.db.models import ICD10
from app.db.database import SessionLocal
from app.models.terminology import ICD10Code
from app.services.redis_service import redis_service
from app.services.search_logger import search_logger
import logging
import time

logger = logging.getLogger(__name__)


class ICD10Service:
    async def search_codes(self, query: str, limit: int = 10) -> List[ICD10Code]:
        """Search ICD-10 codes from database with caching"""
        start_time = time.time()
        cache_key = f"icd10:search:{query.lower()}:{limit}"
        
        # Check cache first
        cached_result = redis_service.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for ICD-10 search: {query}")
            codes = [ICD10Code(**code) for code in cached_result]
            response_time = (time.time() - start_time) * 1000
            search_logger.log_search(query, len(codes), response_time, cache_hit=True)
            return codes
        
        try:
            db: Session = SessionLocal()
            
            # Search by code or term
            results = db.query(ICD10).filter(
                or_(
                    ICD10.code.ilike(f"%{query}%"),
                    ICD10.term.ilike(f"%{query}%")
                ),
                ICD10.active == True
            ).limit(limit).all()
            
            codes = []
            for result in results:
                code = ICD10Code(
                    code=result.code,
                    term=result.term,
                    chapter=result.chapter or "",
                    parent_code=result.parent_code
                )
                codes.append(code)
            
            db.close()
            
            # Cache the results
            cache_data = [code.dict() for code in codes]
            redis_service.set(cache_key, cache_data)
            
            # Log search
            response_time = (time.time() - start_time) * 1000
            search_logger.log_search(query, len(codes), response_time, cache_hit=False)
            
            logger.info(f"ICD-10 search successful for query: {query}")
            return codes
            
        except Exception as e:
            logger.error(f"ICD-10 search error: {e}")
            return []
    
    async def get_code_by_id(self, code: str) -> Optional[ICD10Code]:
        """Get ICD-10 code by ID from database"""
        cache_key = f"icd10:code:{code}"
        
        # Check cache first
        cached_result = redis_service.get(cache_key)
        if cached_result:
            return ICD10Code(**cached_result)
        
        try:
            db: Session = SessionLocal()
            result = db.query(ICD10).filter(
                ICD10.code == code,
                ICD10.active == True
            ).first()
            
            if result:
                icd_code = ICD10Code(
                    code=result.code,
                    term=result.term,
                    chapter=result.chapter or "",
                    parent_code=result.parent_code
                )
                
                # Cache the result
                redis_service.set(cache_key, icd_code.dict())
                
                db.close()
                return icd_code
            
            db.close()
            return None
            
        except Exception as e:
            logger.error(f"ICD-10 code fetch error: {e}")
            return None


icd10_service = ICD10Service()