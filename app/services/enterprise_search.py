from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text, func, or_, and_
from sqlalchemy.exc import SQLAlchemyError
from app.db.database import SessionLocal
from app.db.models import ICD10
from app.models.terminology import ICD10Code
from app.services.redis_service import redis_service
from app.core.exceptions import DatabaseError
import logging
import time

logger = logging.getLogger(__name__)


class EnterpriseSearchService:
    """Enterprise-grade medical terminology search with advanced features"""
    
    def __init__(self):
        self.cache_ttl = 3600  # 1 hour
        self.max_results = 100
    
    async def advanced_icd10_search(
        self, 
        query: str, 
        limit: int = 10,
        chapter_filter: Optional[str] = None,
        include_inactive: bool = False,
        fuzzy_threshold: float = 0.3
    ) -> Dict[str, Any]:
        """Advanced ICD-10 search with multiple algorithms"""
        
        start_time = time.time()
        cache_key = f"icd10:advanced:{query.lower()}:{limit}:{chapter_filter}:{include_inactive}"
        
        # Check cache
        cached_result = redis_service.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for advanced ICD-10 search: {query}")
            return cached_result
        
        try:
            db: Session = SessionLocal()
            if not db:
                raise DatabaseError("Failed to create database session")
            
            # Build base query
            base_query = db.query(ICD10)
            
            if not include_inactive:
                base_query = base_query.filter(ICD10.active == True)
            
            if chapter_filter:
                base_query = base_query.filter(ICD10.chapter.ilike(f"%{chapter_filter}%"))
            
            # 1. Exact code match (highest priority)
            exact_matches = base_query.filter(
                ICD10.code.ilike(f"{query}%")
            ).limit(5).all()
            
            # 2. Term prefix match
            term_prefix = base_query.filter(
                func.lower(ICD10.term).like(f"{query.lower()}%")
            ).limit(10).all()
            
            # 3. Fuzzy search using SQLAlchemy ORM (safe from SQL injection)
            fuzzy_query = base_query.filter(
                or_(
                    func.similarity(ICD10.term, query) > fuzzy_threshold,
                    func.similarity(ICD10.code, query) > fuzzy_threshold
                )
            ).order_by(
                (func.similarity(ICD10.term, query) + func.similarity(ICD10.code, query)).desc(),
                ICD10.code
            ).limit(limit * 2)
            
            fulltext_results = fuzzy_query.all()
            
            # Combine and deduplicate results
            all_results = []
            seen_codes = set()
            
            # Add exact matches first
            for result in exact_matches:
                if result.code not in seen_codes:
                    all_results.append({
                        'code': result.code,
                        'term': result.term,
                        'chapter': result.chapter,
                        'parent_code': result.parent_code,
                        'match_type': 'exact_code',
                        'confidence': 1.0
                    })
                    seen_codes.add(result.code)
            
            # Add term prefix matches
            for result in term_prefix:
                if result.code not in seen_codes:
                    all_results.append({
                        'code': result.code,
                        'term': result.term,
                        'chapter': result.chapter,
                        'parent_code': result.parent_code,
                        'match_type': 'term_prefix',
                        'confidence': 0.9
                    })
                    seen_codes.add(result.code)
            
            # Add fuzzy matches
            for result in fulltext_results:
                if result.code not in seen_codes:
                    # Calculate confidence score
                    term_sim = db.execute(
                        func.similarity(ICD10.term, query)
                    ).scalar() or 0
                    code_sim = db.execute(
                        func.similarity(ICD10.code, query)
                    ).scalar() or 0
                    confidence = (term_sim + code_sim) / 2
                    
                    all_results.append({
                        'code': result.code,
                        'term': result.term,
                        'chapter': result.chapter,
                        'parent_code': result.parent_code,
                        'match_type': 'fuzzy',
                        'confidence': float(confidence)
                    })
                    seen_codes.add(result.code)
            
            # Limit results
            final_results = all_results[:limit]
            
            db.close()
            
            # Prepare response
            response = {
                'results': final_results,
                'total_count': len(final_results),
                'query_time_ms': round((time.time() - start_time) * 1000, 2),
                'search_metadata': {
                    'exact_matches': len(exact_matches),
                    'prefix_matches': len(term_prefix),
                    'fuzzy_matches': len(fulltext_results),
                    'chapter_filter': chapter_filter,
                    'fuzzy_threshold': fuzzy_threshold
                }
            }
            
            # Cache results
            redis_service.set(cache_key, response, ttl=self.cache_ttl)
            
            logger.info(f"Advanced ICD-10 search completed: {query} -> {len(final_results)} results")
            return response
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in advanced ICD-10 search: {e}")
            raise DatabaseError(f"Database query failed: {str(e)}")
        except Exception as e:
            logger.error(f"Advanced ICD-10 search error: {e}")
            raise Exception(f"Search service error: {str(e)}")
        finally:
            if 'db' in locals():
                db.close()
    
    async def get_icd10_hierarchy(self, code: str) -> Dict[str, Any]:
        """Get ICD-10 code with its hierarchical context"""
        cache_key = f"icd10:hierarchy:{code}"
        
        cached_result = redis_service.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            db: Session = SessionLocal()
            
            # Get the main code
            main_code = db.query(ICD10).filter(ICD10.code == code).first()
            if not main_code:
                return {'error': 'Code not found'}
            
            # Get parent codes (hierarchy up)
            parents = []
            if main_code.parent_code:
                parent = db.query(ICD10).filter(ICD10.code == main_code.parent_code).first()
                if parent:
                    parents.append({
                        'code': parent.code,
                        'term': parent.term,
                        'level': 'parent'
                    })
            
            # Get child codes (hierarchy down)
            children = db.query(ICD10).filter(
                ICD10.parent_code == code,
                ICD10.active == True
            ).limit(20).all()
            
            child_list = [{
                'code': child.code,
                'term': child.term,
                'level': 'child'
            } for child in children]
            
            # Get siblings (same parent)
            siblings = []
            if main_code.parent_code:
                siblings_query = db.query(ICD10).filter(
                    ICD10.parent_code == main_code.parent_code,
                    ICD10.code != code,
                    ICD10.active == True
                ).limit(10).all()
                
                siblings = [{
                    'code': sibling.code,
                    'term': sibling.term,
                    'level': 'sibling'
                } for sibling in siblings_query]
            
            db.close()
            
            result = {
                'code': main_code.code,
                'term': main_code.term,
                'chapter': main_code.chapter,
                'parents': parents,
                'children': child_list,
                'siblings': siblings,
                'hierarchy_depth': len(parents) + 1
            }
            
            redis_service.set(cache_key, result, ttl=self.cache_ttl)
            return result
            
        except Exception as e:
            logger.error(f"ICD-10 hierarchy error: {e}")
            return {'error': str(e)}
    
    async def clinical_decision_support(self, symptoms: List[str]) -> Dict[str, Any]:
        """Clinical decision support based on symptoms"""
        cache_key = f"cds:symptoms:{':'.join(sorted(symptoms))}"
        
        cached_result = redis_service.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            db: Session = SessionLocal()
            
            # Search for each symptom
            all_matches = []
            for symptom in symptoms:
                matches = await self.advanced_icd10_search(symptom, limit=5)
                for match in matches.get('results', []):
                    match['symptom'] = symptom
                    all_matches.append(match)
            
            # Group by ICD-10 code and calculate relevance
            code_scores = {}
            for match in all_matches:
                code = match['code']
                if code not in code_scores:
                    code_scores[code] = {
                        'code': code,
                        'term': match['term'],
                        'chapter': match['chapter'],
                        'matching_symptoms': [],
                        'total_confidence': 0,
                        'symptom_count': 0
                    }
                
                code_scores[code]['matching_symptoms'].append(match['symptom'])
                code_scores[code]['total_confidence'] += match['confidence']
                code_scores[code]['symptom_count'] += 1
            
            # Calculate final scores
            suggestions = []
            for code_data in code_scores.values():
                avg_confidence = code_data['total_confidence'] / code_data['symptom_count']
                symptom_coverage = code_data['symptom_count'] / len(symptoms)
                
                final_score = (avg_confidence * 0.7) + (symptom_coverage * 0.3)
                
                suggestions.append({
                    'code': code_data['code'],
                    'term': code_data['term'],
                    'chapter': code_data['chapter'],
                    'confidence_score': round(final_score, 3),
                    'matching_symptoms': code_data['matching_symptoms'],
                    'symptom_coverage': round(symptom_coverage, 2)
                })
            
            # Sort by confidence
            suggestions.sort(key=lambda x: x['confidence_score'], reverse=True)
            
            db.close()
            
            result = {
                'suggestions': suggestions[:10],
                'input_symptoms': symptoms,
                'total_suggestions': len(suggestions)
            }
            
            redis_service.set(cache_key, result, ttl=1800)  # 30 min cache
            return result
            
        except Exception as e:
            logger.error(f"Clinical decision support error: {e}")
            return {'error': str(e)}


# Global enterprise search service
enterprise_search = EnterpriseSearchService()[str]) -> Dict[str, Any]:
        """Clinical decision support based on symptoms"""
        cache_key = f"cds:symptoms:{':'.join(sorted(symptoms))}"
        
        cached_result = redis_service.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            db: Session = SessionLocal()
            
            # Search for each symptom
            all_matches = []
            for symptom in symptoms:
                matches = await self.advanced_icd10_search(symptom, limit=5)
                for match in matches.get('results', []):
                    match['symptom'] = symptom
                    all_matches.append(match)
            
            # Group by ICD-10 code and calculate relevance
            code_scores = {}
            for match in all_matches:
                code = match['code']
                if code not in code_scores:
                    code_scores[code] = {
                        'code': code,
                        'term': match['term'],
                        'chapter': match['chapter'],
                        'matching_symptoms': [],
                        'total_confidence': 0,
                        'symptom_count': 0
                    }
                
                code_scores[code]['matching_symptoms'].append(match['symptom'])
                code_scores[code]['total_confidence'] += match['confidence']
                code_scores[code]['symptom_count'] += 1
            
            # Calculate final scores
            suggestions = []
            for code_data in code_scores.values():
                avg_confidence = code_data['total_confidence'] / code_data['symptom_count']
                symptom_coverage = code_data['symptom_count'] / len(symptoms)
                
                final_score = (avg_confidence * 0.7) + (symptom_coverage * 0.3)
                
                suggestions.append({
                    'code': code_data['code'],
                    'term': code_data['term'],
                    'chapter': code_data['chapter'],
                    'confidence_score': round(final_score, 3),
                    'matching_symptoms': code_data['matching_symptoms'],
                    'symptom_coverage': round(symptom_coverage, 2)
                })
            
            # Sort by confidence
            suggestions.sort(key=lambda x: x['confidence_score'], reverse=True)
            
            db.close()
            
            result = {
                'suggestions': suggestions[:10],
                'input_symptoms': symptoms,
                'total_suggestions': len(suggestions)
            }
            
            redis_service.set(cache_key, result, ttl=1800)  # 30 min cache
            return result
            
        except Exception as e:
            logger.error(f"Clinical decision support error: {e}")
            return {'error': str(e)}


# Global enterprise search service
enterprise_search = EnterpriseSearchService()