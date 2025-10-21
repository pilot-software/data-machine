"""Base repository with dependency injection"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import ITerminologyRepository

class BaseRepository(ITerminologyRepository):
    """Base repository with common functionality"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def execute_query(self, query: str, params: dict = None) -> Any:
        """Execute raw query with parameters"""
        result = await self.session.execute(query, params or {})
        return result
    
    async def commit(self):
        """Commit transaction"""
        await self.session.commit()
    
    async def rollback(self):
        """Rollback transaction"""
        await self.session.rollback()