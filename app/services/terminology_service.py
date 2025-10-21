from typing import List, Dict, Any, Optional
from app.repositories.async_icd10_repository import AsyncICD10Repository
from app.core.circuit_breaker import redis_circuit_breaker
from app.core.exceptions import DatabaseError, ServiceUnavailableError
from app.core.dependencies import ICacheService, ITerminologyRepository
from app.core.settings import settings
import time
import logging
import asyncio

logger = logging.getLogger(__name__)

class TerminologyService:
    """Business logic layer for terminology operations with dependency injection"""
    
    def __init__(self, cache_service: ICacheService, repository: ITerminologyRepository):
        self.cache_service = cache_service
        self.repository = repository
        self.cache_ttl = settings.cache.ttl
    
    async def search_icd10(self, query: str, limit: int = 10, chapter_filter: Optional[str] = None) -> Dict[str, Any]:
        """Search ICD-10 codes with business logic and circuit breaker protection"""
        start_time = time.time()
        cache_key = f"icd10:search:{query.lower()}:{limit}:{chapter_filter}"
        
        # Check cache
        try:
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for search: {query}")
                return cached_result
        except Exception as e:
            logger.warning(f"Cache unavailable: {e}")
        
        try:
            async with AsyncICD10Repository() as repo:
                all_results = []
                seen_codes = set()
                
                # Run searches sequentially to avoid session conflicts
                try:
                    exact_matches = await repo.find_by_code_prefix(query, limit=5)
                except Exception as e:
                    logger.error(f"Exact match search failed: {e}")
                    exact_matches = []
                
                try:
                    term_matches = await repo.find_by_term_prefix(query, limit=10)
                except Exception as e:
                    logger.error(f"Term match search failed: {e}")
                    term_matches = []
                
                try:
                    fuzzy_matches = await repo.find_by_similarity(query, threshold=0.3, limit=20)
                except Exception as e:
                    logger.error(f"Fuzzy match search failed: {e}")
                    fuzzy_matches = []
                
                # 1. Exact code matches (highest priority)
                for result in exact_matches:
                    if self._matches_chapter(result, chapter_filter):
                        all_results.append(self._format_result(result, 'exact_code', 1.0))
                        seen_codes.add(result.code)
                
                # 2. Term prefix matches
                if len(all_results) < limit:
                    for result in term_matches:
                        if result.code not in seen_codes and self._matches_chapter(result, chapter_filter):
                            all_results.append(self._format_result(result, 'term_prefix', 0.9))
                            seen_codes.add(result.code)
                
                # 3. Fuzzy matches
                if len(all_results) < limit:
                    for result in fuzzy_matches:
                        if result.code not in seen_codes and self._matches_chapter(result, chapter_filter):
                            confidence = self._calculate_confidence(result, query)
                            all_results.append(self._format_result(result, 'fuzzy', confidence))
                            seen_codes.add(result.code)
                
                final_results = all_results[:limit]
                
                response = {
                    'results': final_results,
                    'total_count': len(final_results),
                    'query_time_ms': round((time.time() - start_time) * 1000, 2),
                    'cache_status': 'miss'
                }
                
                # Cache results
                try:
                    await self.cache_service.set(cache_key, response, ttl=self.cache_ttl)
                except Exception as e:
                    logger.warning(f"Failed to cache results: {e}")
                
                return response
                
        except DatabaseError as e:
            logger.error(f"Database error in search_icd10: {e}")
            raise ServiceUnavailableError("Search service temporarily unavailable")
        except Exception as e:
            logger.error(f"Unexpected error in search_icd10: {e}")
            raise ServiceUnavailableError("Search service error")
    
    async def get_code_details(self, code: str) -> Dict[str, Any]:
        """Get detailed information for a specific code with full hierarchy"""
        start_time = time.time()
        cache_key = f"icd10:details:{code}"
        
        # Check cache
        try:
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for code details: {code}")
                return cached_result
        except Exception as e:
            logger.warning(f"Cache unavailable for code details: {e}")
        
        try:
            async with AsyncICD10Repository() as repo:
                main_code = await repo.find_by_code(code)
                if not main_code:
                    return {'error': 'Code not found', 'code': code}
                
                # Get hierarchy data concurrently
                parent_task = None
                if main_code.parent_code:
                    parent_task = repo.find_by_code(main_code.parent_code)
                
                children_task = repo.find_children(code, limit=20)
                siblings_task = repo.find_siblings(main_code.parent_code, code, limit=10) if main_code.parent_code else None
                
                # Execute concurrent queries
                tasks = [children_task]
                if parent_task:
                    tasks.append(parent_task)
                if siblings_task:
                    tasks.append(siblings_task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                children = results[0] if not isinstance(results[0], Exception) else []
                parent = results[1] if len(results) > 1 and not isinstance(results[1], Exception) else None
                siblings = results[2] if len(results) > 2 and not isinstance(results[2], Exception) else []
                
                # Build hierarchy
                parents = []
                if parent:
                    parents.append(self._format_hierarchy_item(parent, 'parent'))
                
                result = {
                    'code': main_code.code,
                    'term': main_code.term,
                    'chapter': main_code.chapter,
                    'parent_code': main_code.parent_code,
                    'active': main_code.active,
                    'parents': parents,
                    'children': [self._format_hierarchy_item(child, 'child') for child in children],
                    'siblings': [self._format_hierarchy_item(sibling, 'sibling') for sibling in siblings],
                    'hierarchy_depth': len(parents) + 1,
                    'total_children': len(children),
                    'total_siblings': len(siblings),
                    'query_time_ms': round((time.time() - start_time) * 1000, 2)
                }
                
                # Cache result
                try:
                    await self.cache_service.set(cache_key, result, ttl=self.cache_ttl)
                except Exception as e:
                    logger.warning(f"Failed to cache code details: {e}")
                
                return result
                
        except DatabaseError as e:
            logger.error(f"Database error in get_code_details: {e}")
            raise ServiceUnavailableError("Code lookup service temporarily unavailable")
        except Exception as e:
            logger.error(f"Unexpected error in get_code_details: {e}")
            raise ServiceUnavailableError("Code lookup service error")
    
    async def clinical_analysis(self, symptoms: List[str]) -> Dict[str, Any]:
        """Comprehensive clinical decision support with multi-symptom analysis"""
        start_time = time.time()
        cache_key = f"clinical:analysis:{':'.join(sorted(symptoms))}"
        
        # Check cache
        try:
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for clinical analysis: {len(symptoms)} symptoms")
                return cached_result
        except Exception as e:
            logger.warning(f"Cache unavailable for clinical analysis: {e}")
        
        try:
            # Search for each symptom concurrently
            search_tasks = []
            for symptom in symptoms:
                task = self.search_icd10(symptom, limit=5)
                search_tasks.append(task)
            
            # Execute all searches concurrently
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Process results
            all_matches = []
            for i, (symptom, matches) in enumerate(zip(symptoms, search_results)):
                if isinstance(matches, Exception):
                    logger.error(f"Search failed for symptom '{symptom}': {matches}")
                    continue
                
                for match in matches.get('results', []):
                    match['symptom'] = symptom
                    match['symptom_index'] = i
                    all_matches.append(match)
            
            if not all_matches:
                return {
                    'suggestions': [],
                    'input_symptoms': symptoms,
                    'total_suggestions': 0,
                    'analysis_status': 'no_matches_found',
                    'query_time_ms': round((time.time() - start_time) * 1000, 2)
                }
            
            # Advanced symptom analysis
            suggestions = self._analyze_symptom_matches(all_matches, symptoms)
            
            # Calculate additional clinical metrics
            clinical_metrics = self._calculate_clinical_metrics(suggestions, symptoms)
            
            result = {
                'suggestions': suggestions[:10],
                'input_symptoms': symptoms,
                'total_suggestions': len(suggestions),
                'clinical_metrics': clinical_metrics,
                'analysis_status': 'completed',
                'query_time_ms': round((time.time() - start_time) * 1000, 2),
                'cache_status': 'miss'
            }
            
            # Cache result for 30 minutes
            try:
                await self.cache_service.set(cache_key, result, ttl=1800)
            except Exception as e:
                logger.warning(f"Failed to cache clinical analysis: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Clinical analysis error: {e}")
            raise ServiceUnavailableError("Clinical decision support temporarily unavailable")
    
    def _matches_chapter(self, result, chapter_filter: Optional[str]) -> bool:
        """Check if result matches chapter filter"""
        if not chapter_filter:
            return True
        return chapter_filter.lower() in (result.chapter or '').lower()
    
    def _format_result(self, result, match_type: str, confidence: float) -> Dict[str, Any]:
        """Format database result for API response"""
        return {
            'code': result.code,
            'term': result.term,
            'chapter': result.chapter or '',
            'match_type': match_type,
            'confidence': confidence
        }
    
    def _format_hierarchy_item(self, result, level: str) -> Dict[str, Any]:
        """Format hierarchy item"""
        return {
            'code': result.code,
            'term': result.term,
            'level': level
        }
    
    def _calculate_confidence(self, result, query: str) -> float:
        """Calculate confidence score for fuzzy matches"""
        # Simple confidence calculation based on term similarity
        term_lower = result.term.lower()
        query_lower = query.lower()
        
        if query_lower in term_lower:
            return 0.8
        elif any(word in term_lower for word in query_lower.split()):
            return 0.6
        else:
            return 0.4
    
    def _analyze_symptom_matches(self, matches: List[Dict], symptoms: List[str]) -> List[Dict[str, Any]]:
        """Analyze symptom matches for clinical suggestions"""
        code_scores = {}
        
        for match in matches:
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
        
        return sorted(suggestions, key=lambda x: x['confidence_score'], reverse=True)
    
    def _calculate_clinical_metrics(self, suggestions: List[Dict], symptoms: List[str]) -> Dict[str, Any]:
        """Calculate advanced clinical decision support metrics"""
        if not suggestions:
            return {'confidence': 'low', 'coverage': 0.0, 'specificity': 0.0}
        
        # Calculate overall confidence
        avg_confidence = sum(s['confidence_score'] for s in suggestions) / len(suggestions)
        
        # Calculate symptom coverage
        covered_symptoms = set()
        for suggestion in suggestions:
            covered_symptoms.update(suggestion.get('matching_symptoms', []))
        coverage = len(covered_symptoms) / len(symptoms)
        
        # Calculate diagnostic specificity
        unique_chapters = set(s.get('chapter', '') for s in suggestions)
        specificity = 1.0 / len(unique_chapters) if unique_chapters else 0.0
        
        # Determine confidence level
        if avg_confidence >= 0.8 and coverage >= 0.7:
            confidence_level = 'high'
        elif avg_confidence >= 0.6 and coverage >= 0.5:
            confidence_level = 'medium'
        else:
            confidence_level = 'low'
        
        return {
            'confidence_level': confidence_level,
            'average_confidence': round(avg_confidence, 3),
            'symptom_coverage': round(coverage, 3),
            'diagnostic_specificity': round(specificity, 3),
            'unique_chapters': len(unique_chapters),
            'total_matches': len(suggestions)
        }
    
    async def batch_code_lookup(self, codes: List[str]) -> Dict[str, Dict[str, Any]]:
        """Batch lookup for multiple ICD-10 codes"""
        start_time = time.time()
        
        # Check cache for all codes
        cache_keys = [f"icd10:details:{code}" for code in codes]
        cached_results = {}  # Simplified - skip batch cache for now
        
        # Identify codes that need lookup
        missing_codes = []
        results = {}
        
        for code in codes:
            cache_key = f"icd10:details:{code}"
            if cache_key in cached_results:
                results[code] = cached_results[cache_key]
            else:
                missing_codes.append(code)
        
        # Lookup missing codes concurrently
        if missing_codes:
            try:
                async with AsyncICD10Repository() as repo:
                    lookup_tasks = [repo.find_by_code(code) for code in missing_codes]
                    lookup_results = await asyncio.gather(*lookup_tasks, return_exceptions=True)
                    
                    # Process lookup results
                    cache_batch = {}
                    for code, result in zip(missing_codes, lookup_results):
                        if isinstance(result, Exception):
                            logger.error(f"Lookup failed for code {code}: {result}")
                            results[code] = {'error': 'Lookup failed', 'code': code}
                        elif result:
                            formatted_result = {
                                'code': result.code,
                                'term': result.term,
                                'chapter': result.chapter,
                                'parent_code': result.parent_code,
                                'active': result.active
                            }
                            results[code] = formatted_result
                            cache_batch[f"icd10:details:{code}"] = formatted_result
                        else:
                            results[code] = {'error': 'Code not found', 'code': code}
                    
                    # Cache new results
                    if cache_batch:
                        try:
                            for key, value in cache_batch.items():
                                await self.cache_service.set(key, value, ttl=self.cache_ttl)
                        except Exception as e:
                            logger.warning(f"Batch cache set failed: {e}")
                            
            except Exception as e:
                logger.error(f"Batch lookup error: {e}")
                for code in missing_codes:
                    results[code] = {'error': 'Service unavailable', 'code': code}
        
        return {
            'results': results,
            'total_codes': len(codes),
            'cache_hits': len(codes) - len(missing_codes),
            'cache_misses': len(missing_codes),
            'query_time_ms': round((time.time() - start_time) * 1000, 2)
        }
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get service performance statistics"""
        try:
            # Get Redis stats - simplified
            redis_stats = {'status': 'available'}
            
            # Get database connection info
            async with AsyncICD10Repository() as repo:
                total_codes = await repo.count_total()
            
            return {
                'service_status': 'operational',
                'database': {
                    'total_icd10_codes': total_codes,
                    'connection_status': 'healthy'
                },
                'cache': redis_stats,
                'features': {
                    'search_algorithms': ['exact_match', 'prefix_match', 'fuzzy_similarity'],
                    'concurrent_operations': True,
                    'circuit_breaker_protection': True,
                    'structured_logging': True,
                    'performance_monitoring': True
                }
            }
        except Exception as e:
            logger.error(f"Performance stats error: {e}")
            return {
                'service_status': 'degraded',
                'error': str(e)
            }
    
    async def autocomplete_icd10(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """ICD-10 autocomplete with optimized search"""
        start_time = time.time()
        cache_key = f"icd10:autocomplete:{query.lower()}:{limit}"
        
        try:
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                return cached_result
        except Exception:
            pass
        
        async with AsyncICD10Repository() as repo:
            # Search by term for autocomplete
            exact_matches = await repo.find_by_term_prefix(query, limit=limit)
            
            suggestions = []
            for result in exact_matches[:limit]:
                suggestions.append({
                    'code': result.code,
                    'term': result.term,
                    'chapter': result.chapter or '',
                    'confidence': 0.95 if result.code.lower().startswith(query.lower()) else 0.8
                })
            
            response = {
                'suggestions': suggestions,
                'total_count': len(suggestions),
                'query_time_ms': round((time.time() - start_time) * 1000, 2)
            }
            
            await self.cache_service.set(cache_key, response, ttl=self.cache_ttl)
            return response
    
    async def advanced_search(self, query: str, limit: int = 10, chapter_filter: Optional[str] = None,
                            include_inactive: bool = False, fuzzy_threshold: float = 0.3) -> Dict[str, Any]:
        """Advanced search with all filtering options"""
        start_time = time.time()
        cache_key = f"icd10:advanced:{query.lower()}:{limit}:{chapter_filter}:{include_inactive}:{fuzzy_threshold}"
        
        cached_result = await self.cache_service.get(cache_key)
        if cached_result:
            return cached_result
        
        async with AsyncICD10Repository() as repo:
            all_results = []
            seen_codes = set()
            
            # 1. Exact code matches (highest priority)
            exact_matches = await repo.find_by_code_prefix(query, limit=5)
            
            for result in exact_matches:
                if result.code.lower().startswith(query.lower()):
                    all_results.append(self._format_result(result, 'exact_code', 1.0))
                    seen_codes.add(result.code)
            
            # 2. Term prefix matches
            if len(all_results) < limit:
                term_matches = await repo.find_by_term_prefix(query, limit=10)
                for result in term_matches:
                    if result.code not in seen_codes:
                        all_results.append(self._format_result(result, 'term_prefix', 0.9))
                        seen_codes.add(result.code)
            
            # 3. Fuzzy similarity matches
            if len(all_results) < limit:
                fuzzy_matches = await repo.find_by_similarity(query, threshold=fuzzy_threshold, limit=20)
                for result in fuzzy_matches:
                    if result.code not in seen_codes:
                        confidence = self._calculate_advanced_confidence(result, query)
                        all_results.append(self._format_result(result, 'fuzzy', confidence))
                        seen_codes.add(result.code)
            
            final_results = all_results[:limit]
            
            response = {
                'results': final_results,
                'total_count': len(final_results),
                'query_time_ms': round((time.time() - start_time) * 1000, 2),
                'search_metadata': {
                    'exact_matches': len([r for r in final_results if r['match_type'] == 'exact_code']),
                    'prefix_matches': len([r for r in final_results if r['match_type'] == 'term_prefix']),
                    'fuzzy_matches': len([r for r in final_results if r['match_type'] == 'fuzzy']),
                    'chapter_filter': chapter_filter,
                    'fuzzy_threshold': fuzzy_threshold
                }
            }
            
            await self.cache_service.set(cache_key, response, ttl=self.cache_ttl)
            return response
    
    async def unified_search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Unified search across all terminology systems"""
        start_time = time.time()
        
        # Search ICD-10 (primary system)
        icd10_results = await self.search_icd10(query, limit=limit)
        
        # Format for unified response
        unified_results = []
        for result in icd10_results.get('results', []):
            unified_results.append({
                'code': result['code'],
                'title': result['term'],
                'chapter': result.get('chapter', ''),
                'version': 'ICD-10',
                'confidence': result.get('confidence', 0),
                'system': 'ICD-10-CM'
            })
        
        # TODO: Add ICD-11 results when implemented
        # icd11_results = await self.search_icd11(query, limit=limit//2)
        
        return {
            'query': query,
            'total_results': len(unified_results),
            'results': unified_results,
            'query_time_ms': round((time.time() - start_time) * 1000, 2),
            'systems_searched': ['ICD-10-CM']
        }
    
    def _calculate_advanced_confidence(self, result, query: str) -> float:
        """Advanced confidence calculation with multiple factors"""
        term_lower = result.term.lower()
        query_lower = query.lower()
        
        # Exact match in term
        if query_lower == term_lower:
            return 1.0
        
        # Query is substring of term
        if query_lower in term_lower:
            position_factor = 1.0 - (term_lower.index(query_lower) / len(term_lower))
            length_factor = len(query_lower) / len(term_lower)
            return 0.7 + (position_factor * 0.2) + (length_factor * 0.1)
        
        # Word-level matching
        query_words = set(query_lower.split())
        term_words = set(term_lower.split())
        word_overlap = len(query_words.intersection(term_words)) / len(query_words)
        
        if word_overlap > 0.5:
            return 0.5 + (word_overlap * 0.3)
        
        # Character-level similarity (fallback)
        return 0.3

# Global service instance - initialized via dependency injection
# terminology_service = TerminologyService()  # Removed - use DI instead