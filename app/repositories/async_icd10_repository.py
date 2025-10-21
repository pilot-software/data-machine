from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.exc import SQLAlchemyError
from app.db.models import ICD10
from app.db.database import AsyncSessionLocal
from app.core.circuit_breaker import database_circuit_breaker
from app.core.exceptions import DatabaseError
from app.repositories.base_repository import BaseRepository
import logging

logger = logging.getLogger(__name__)

class AsyncICD10Repository(BaseRepository):
    """Async repository for ICD-10 codes with circuit breaker protection"""
    
    def __init__(self, session: Optional[AsyncSession] = None):
        if session:
            super().__init__(session)
        self.session: Optional[AsyncSession] = session
    
    async def search_codes(self, query: str, limit: int) -> list:
        """Implementation of abstract method"""
        return await self.find_by_term_prefix(query, limit)
    
    async def __aenter__(self):
        self.session = AsyncSessionLocal()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def find_by_code(self, code: str) -> Optional[ICD10]:
        """Find ICD-10 code by exact match with circuit breaker"""
        async def _query():
            stmt = select(ICD10).where(ICD10.code == code)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        
        try:
            return await database_circuit_breaker.call(_query)
        except SQLAlchemyError as e:
            logger.error(f"Database error in find_by_code: {e}")
            raise DatabaseError(f"Failed to find code {code}")
        except Exception as e:
            logger.error(f"Circuit breaker error in find_by_code: {e}")
            raise DatabaseError("Database service unavailable")
    
    async def find_by_code_prefix(self, prefix: str, limit: int = 10) -> List[ICD10]:
        """Find codes starting with prefix"""
        async def _query():
            stmt = select(ICD10).where(
                ICD10.code.ilike(f"{prefix}%")
            ).limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        
        try:
            return await database_circuit_breaker.call(_query)
        except SQLAlchemyError as e:
            logger.error(f"Database error in find_by_code_prefix: {e}")
            raise DatabaseError(f"Failed to search codes with prefix {prefix}")
        except Exception as e:
            logger.error(f"Circuit breaker error in find_by_code_prefix: {e}")
            raise DatabaseError("Database service unavailable")
    
    async def find_by_term_prefix(self, term: str, limit: int = 10) -> List[ICD10]:
        """Find codes by term containing search term"""
        async def _query():
            stmt = select(ICD10).where(
                func.lower(ICD10.term).like(f"%{term.lower()}%")
            ).limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        
        try:
            return await database_circuit_breaker.call(_query)
        except SQLAlchemyError as e:
            logger.error(f"Database error in find_by_term_prefix: {e}")
            raise DatabaseError(f"Failed to search terms with prefix {term}")
        except Exception as e:
            logger.error(f"Circuit breaker error in find_by_term_prefix: {e}")
            raise DatabaseError("Database service unavailable")
    
    async def find_by_similarity(self, query: str, threshold: float = 0.3, limit: int = 20) -> List[ICD10]:
        """Find codes using similarity matching"""
        async def _query():
            stmt = select(ICD10).where(
                or_(
                    func.similarity(ICD10.term, query) > threshold,
                    func.similarity(ICD10.code, query) > threshold
                )
            ).order_by(
                (func.similarity(ICD10.term, query) + func.similarity(ICD10.code, query)).desc()
            ).limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        
        try:
            return await database_circuit_breaker.call(_query)
        except SQLAlchemyError as e:
            logger.error(f"Database error in find_by_similarity: {e}")
            raise DatabaseError(f"Failed to perform similarity search for {query}")
        except Exception as e:
            logger.error(f"Circuit breaker error in find_by_similarity: {e}")
            raise DatabaseError("Database service unavailable")
    
    async def find_children(self, parent_code: str, limit: int = 20) -> List[ICD10]:
        """Find child codes"""
        async def _query():
            # icd10_codes table doesn't have parent_code, return empty
            return []
        
        try:
            return await database_circuit_breaker.call(_query)
        except Exception as e:
            logger.error(f"Circuit breaker error in find_children: {e}")
            raise DatabaseError("Database service unavailable")
    
    async def find_siblings_old(self, parent_code: str, exclude_code: str, limit: int = 10) -> List[ICD10]:
        """Find sibling codes - not supported"""
        return []
        
        try:
            return await database_circuit_breaker.call(_query)
        except SQLAlchemyError as e:
            logger.error(f"Database error in find_children: {e}")
            raise DatabaseError(f"Failed to find children for {parent_code}")
        except Exception as e:
            logger.error(f"Circuit breaker error in find_children: {e}")
            raise DatabaseError("Database service unavailable")
    
    async def find_siblings(self, parent_code: str, exclude_code: str, limit: int = 10) -> List[ICD10]:
        """Find sibling codes - not supported"""
        return []
    
    async def count_total(self) -> int:
        """Get total count of codes"""
        async def _query():
            stmt = select(func.count(ICD10.id))
            result = await self.session.execute(stmt)
            return result.scalar()
        
        try:
            return await database_circuit_breaker.call(_query)
        except SQLAlchemyError as e:
            logger.error(f"Database error in count_total: {e}")
            raise DatabaseError("Failed to count total codes")
        except Exception as e:
            logger.error(f"Circuit breaker error in count_total: {e}")
            raise DatabaseError("Database service unavailable")