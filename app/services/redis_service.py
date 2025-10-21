import redis.asyncio as aioredis
import json
import logging
import asyncio
from typing import Optional, Any, Dict, List
from app.core.settings import settings
from app.core.circuit_breaker import redis_circuit_breaker

logger = logging.getLogger(__name__)


class AsyncRedisService:
    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self.connection_pool = None
        self._lock = asyncio.Lock()
    
    async def _connect(self):
        """Establish async Redis connection with connection pooling"""
        try:
            self.connection_pool = aioredis.ConnectionPool.from_url(
                f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
                password=settings.redis_password,
                max_connections=20,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={}
            )
            
            self.redis_client = aioredis.Redis(
                connection_pool=self.connection_pool,
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Async Redis connection established with connection pooling")
            
        except Exception as e:
            logger.error(f"Async Redis connection failed: {e}")
            self.redis_client = None
    
    async def _ensure_connected(self):
        """Ensure Redis connection is established"""
        if not self.redis_client:
            async with self._lock:
                if not self.redis_client:
                    await self._connect()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis with circuit breaker protection"""
        await self._ensure_connected()
        
        if not self.redis_client:
            return None
        
        async def _get():
            value = await self.redis_client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error for key {key}: {e}")
                    return None
            return None
        
        try:
            result = await redis_circuit_breaker.call(_get)
            logger.debug(f"Redis GET: {key} -> {'HIT' if result else 'MISS'}")
            return result
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis with TTL and circuit breaker protection"""
        await self._ensure_connected()
        
        if not self.redis_client:
            return False
        
        async def _set():
            ttl_value = ttl or settings.cache_ttl
            try:
                serialized_value = json.dumps(value, default=str)
            except (TypeError, ValueError) as e:
                logger.error(f"JSON serialization error for key {key}: {e}")
                return False
            
            result = await self.redis_client.setex(key, ttl_value, serialized_value)
            return bool(result)
        
        try:
            result = await redis_circuit_breaker.call(_set)
            logger.debug(f"Redis SET: {key} -> {'SUCCESS' if result else 'FAILED'}")
            return result
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        await self._ensure_connected()
        
        if not self.redis_client:
            return False
        
        async def _delete():
            result = await self.redis_client.delete(key)
            return bool(result)
        
        try:
            result = await redis_circuit_breaker.call(_delete)
            logger.debug(f"Redis DELETE: {key} -> {'SUCCESS' if result else 'NOT_FOUND'}")
            return result
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        await self._ensure_connected()
        
        if not self.redis_client:
            return False
        
        async def _exists():
            result = await self.redis_client.exists(key)
            return bool(result)
        
        try:
            result = await redis_circuit_breaker.call(_exists)
            logger.debug(f"Redis EXISTS: {key} -> {result}")
            return result
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False
    
    async def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple keys from Redis"""
        await self._ensure_connected()
        
        if not self.redis_client or not keys:
            return {}
        
        async def _mget():
            values = await self.redis_client.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        logger.error(f"JSON decode error for key {key}")
            return result
        
        try:
            result = await redis_circuit_breaker.call(_mget)
            logger.debug(f"Redis MGET: {len(keys)} keys -> {len(result)} hits")
            return result
        except Exception as e:
            logger.error(f"Redis MGET error for keys {keys}: {e}")
            return {}
    
    async def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple key-value pairs"""
        await self._ensure_connected()
        
        if not self.redis_client or not mapping:
            return False
        
        async def _mset():
            ttl_value = ttl or settings.cache_ttl
            serialized_mapping = {}
            
            for key, value in mapping.items():
                try:
                    serialized_mapping[key] = json.dumps(value, default=str)
                except (TypeError, ValueError) as e:
                    logger.error(f"JSON serialization error for key {key}: {e}")
                    return False
            
            # Use pipeline for atomic operation
            async with self.redis_client.pipeline() as pipe:
                await pipe.mset(serialized_mapping)
                for key in serialized_mapping.keys():
                    await pipe.expire(key, ttl_value)
                await pipe.execute()
            return True
        
        try:
            result = await redis_circuit_breaker.call(_mset)
            logger.debug(f"Redis MSET: {len(mapping)} keys -> {'SUCCESS' if result else 'FAILED'}")
            return result
        except Exception as e:
            logger.error(f"Redis MSET error: {e}")
            return False
    
    async def flush_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern"""
        await self._ensure_connected()
        
        if not self.redis_client:
            return 0
        
        async def _flush_pattern():
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                return deleted
            return 0
        
        try:
            result = await redis_circuit_breaker.call(_flush_pattern)
            logger.info(f"Redis FLUSH_PATTERN: {pattern} -> {result} keys deleted")
            return result
        except Exception as e:
            logger.error(f"Redis FLUSH_PATTERN error for pattern {pattern}: {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get Redis connection and performance stats"""
        await self._ensure_connected()
        
        if not self.redis_client:
            return {'connected': False, 'error': 'No connection'}
        
        try:
            info = await self.redis_client.info()
            return {
                'connected': True,
                'used_memory': info.get('used_memory_human', 'Unknown'),
                'connected_clients': info.get('connected_clients', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(info)
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {'connected': False, 'error': str(e)}
    
    def _calculate_hit_rate(self, info: Dict) -> float:
        """Calculate cache hit rate"""
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
        if self.connection_pool:
            await self.connection_pool.disconnect()
        logger.info("Redis connection closed")


# Global async Redis service instance
redis_service = AsyncRedisService()