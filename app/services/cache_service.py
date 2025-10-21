"""Cache service implementing ICacheService interface"""

from typing import Any, Optional
import json
import logging
from app.core.dependencies import ICacheService
from app.core.settings import settings

logger = logging.getLogger(__name__)

class RedisCacheService(ICacheService):
    """Redis implementation of cache service"""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.default_ttl = settings.cache.ttl
    
    async def get(self, key: str) -> Any:
        """Get value from cache"""
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache"""
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value)
            await self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

class InMemoryCacheService(ICacheService):
    """In-memory fallback cache service"""
    
    def __init__(self):
        self._cache = {}
        self.max_size = settings.cache.max_size
    
    async def get(self, key: str) -> Any:
        """Get value from memory cache"""
        return self._cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in memory cache"""
        if len(self._cache) >= self.max_size:
            # Simple LRU - remove first item
            self._cache.pop(next(iter(self._cache)))
        
        self._cache[key] = value
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from memory cache"""
        self._cache.pop(key, None)
        return True