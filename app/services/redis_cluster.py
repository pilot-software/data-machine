import redis.asyncio as aioredis
import asyncio
import json
import logging
import time
from typing import List, Dict, Any, Optional
from app.core.settings import settings
from app.core.circuit_breaker import redis_circuit_breaker

logger = logging.getLogger(__name__)

class RedisClusterManager:
    """Redis high availability with sentinel and cluster support"""
    
    def __init__(self):
        self.redis_clients: List[aioredis.Redis] = []
        self.sentinel_client = None
        self.current_master = None
        self.read_replicas: List[aioredis.Redis] = []
        self.memory_monitor = RedisMemoryMonitor()
        self.cache_invalidator = CacheInvalidationManager()
        
    async def setup_redis_sentinel(self):
        """Setup Redis Sentinel for high availability"""
        
        sentinel_hosts = [
            ('redis-sentinel-1', 26379),
            ('redis-sentinel-2', 26379), 
            ('redis-sentinel-3', 26379)
        ]
        
        try:
            from aioredis.sentinel import Sentinel
            
            self.sentinel_client = Sentinel(
                sentinel_hosts,
                socket_timeout=0.5,
                socket_connect_timeout=0.5
            )
            
            # Get master connection
            self.current_master = self.sentinel_client.master_for(
                'mymaster',
                socket_timeout=0.5,
                socket_connect_timeout=0.5,
                decode_responses=True
            )
            
            # Get slave connections for read operations
            slave_client = self.sentinel_client.slave_for(
                'mymaster',
                socket_timeout=0.5,
                socket_connect_timeout=0.5,
                decode_responses=True
            )
            self.read_replicas.append(slave_client)
            
            logger.info("Redis Sentinel setup completed")
            
        except Exception as e:
            logger.error(f"Redis Sentinel setup failed: {e}")
            # Fallback to single Redis instance
            await self._setup_fallback_redis()
    
    async def _setup_fallback_redis(self):
        """Fallback to single Redis instance"""
        
        try:
            redis_client = aioredis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password,
                decode_responses=True,
                max_connections=20,
                retry_on_timeout=True
            )
            
            await redis_client.ping()
            self.current_master = redis_client
            self.read_replicas = [redis_client]  # Use same for reads
            
            logger.info("Fallback Redis connection established")
            
        except Exception as e:
            logger.error(f"Fallback Redis setup failed: {e}")
    
    async def get_write_client(self) -> aioredis.Redis:
        """Get Redis client for write operations"""
        if not self.current_master:
            await self.setup_redis_sentinel()
        return self.current_master
    
    async def get_read_client(self) -> aioredis.Redis:
        """Get Redis client for read operations (load balanced)"""
        if not self.read_replicas:
            await self.setup_redis_sentinel()
        
        # Simple round-robin load balancing
        import random
        return random.choice(self.read_replicas)
    
    async def set_with_invalidation(self, key: str, value: Any, ttl: int = None, 
                                   tags: List[str] = None) -> bool:
        """Set value with cache invalidation tags"""
        
        async def _set_operation():
            client = await self.get_write_client()
            
            # Serialize value
            serialized_value = json.dumps(value, default=str)
            ttl_value = ttl or settings.cache_ttl
            
            # Set main key
            result = await client.setex(key, ttl_value, serialized_value)
            
            # Set invalidation tags
            if tags:
                await self.cache_invalidator.add_tags(key, tags, ttl_value)
            
            return bool(result)
        
        try:
            return await redis_circuit_breaker.call(_set_operation)
        except Exception as e:
            logger.error(f"Redis set with invalidation failed for key {key}: {e}")
            return False
    
    async def get_from_replica(self, key: str) -> Optional[Any]:
        """Get value from read replica"""
        
        async def _get_operation():
            client = await self.get_read_client()
            value = await client.get(key)
            
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    logger.error(f"JSON decode error for key {key}")
                    return None
            return None
        
        try:
            return await redis_circuit_breaker.call(_get_operation)
        except Exception as e:
            logger.error(f"Redis get from replica failed for key {key}: {e}")
            return None
    
    async def invalidate_by_tags(self, tags: List[str]) -> int:
        """Invalidate all cache entries with specified tags"""
        return await self.cache_invalidator.invalidate_by_tags(tags)
    
    async def get_cluster_stats(self) -> Dict[str, Any]:
        """Get comprehensive Redis cluster statistics"""
        
        stats = {
            'cluster_status': 'unknown',
            'master_status': 'unknown',
            'replica_count': len(self.read_replicas),
            'memory_usage': {},
            'performance_metrics': {}
        }
        
        try:
            if self.current_master:
                master_info = await self.current_master.info()
                stats['master_status'] = 'healthy'
                stats['memory_usage'] = await self.memory_monitor.get_memory_stats()
                stats['performance_metrics'] = {
                    'connected_clients': master_info.get('connected_clients', 0),
                    'total_commands_processed': master_info.get('total_commands_processed', 0),
                    'keyspace_hits': master_info.get('keyspace_hits', 0),
                    'keyspace_misses': master_info.get('keyspace_misses', 0)
                }
                
                # Calculate hit rate
                hits = stats['performance_metrics']['keyspace_hits']
                misses = stats['performance_metrics']['keyspace_misses']
                total = hits + misses
                stats['performance_metrics']['hit_rate'] = (hits / total * 100) if total > 0 else 0
            
            stats['cluster_status'] = 'healthy'
            
        except Exception as e:
            logger.error(f"Failed to get cluster stats: {e}")
            stats['cluster_status'] = 'unhealthy'
            stats['error'] = str(e)
        
        return stats

class RedisMemoryMonitor:
    """Monitor Redis memory usage and implement eviction policies"""
    
    def __init__(self):
        self.memory_threshold = 0.8  # 80% memory threshold
        self.monitoring_interval = 60  # Check every minute
        
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get detailed memory usage statistics"""
        
        try:
            redis_client = redis_cluster.current_master
            if not redis_client:
                return {'status': 'unavailable'}
            
            info = await redis_client.info('memory')
            
            used_memory = info.get('used_memory', 0)
            max_memory = info.get('maxmemory', 0)
            
            memory_usage_ratio = (used_memory / max_memory) if max_memory > 0 else 0
            
            return {
                'used_memory_bytes': used_memory,
                'used_memory_human': info.get('used_memory_human', 'Unknown'),
                'max_memory_bytes': max_memory,
                'max_memory_human': info.get('maxmemory_human', 'Unknown'),
                'memory_usage_ratio': round(memory_usage_ratio, 3),
                'memory_fragmentation_ratio': info.get('mem_fragmentation_ratio', 0),
                'status': 'critical' if memory_usage_ratio > self.memory_threshold else 'normal'
            }
            
        except Exception as e:
            logger.error(f"Memory stats collection failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def cleanup_expired_keys(self) -> int:
        """Proactively clean up expired keys"""
        
        try:
            redis_client = redis_cluster.current_master
            if not redis_client:
                return 0
            
            # Get keys that are about to expire (TTL < 60 seconds)
            cleanup_count = 0
            
            async for key in redis_client.scan_iter(match="*", count=1000):
                ttl = await redis_client.ttl(key)
                if 0 < ttl < 60:  # Expires in less than 60 seconds
                    await redis_client.delete(key)
                    cleanup_count += 1
                    
                    # Limit cleanup per iteration to avoid blocking
                    if cleanup_count >= 100:
                        break
            
            logger.info(f"Cleaned up {cleanup_count} expired keys")
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Key cleanup failed: {e}")
            return 0
    
    async def monitor_memory_usage(self):
        """Continuous memory monitoring with alerts"""
        
        while True:
            try:
                stats = await self.get_memory_stats()
                
                if stats.get('status') == 'critical':
                    logger.warning(f"Redis memory usage critical: {stats['memory_usage_ratio']*100:.1f}%")
                    
                    # Trigger cleanup
                    cleaned = await self.cleanup_expired_keys()
                    logger.info(f"Emergency cleanup removed {cleaned} keys")
                    
                    # Force garbage collection
                    redis_client = redis_cluster.current_master
                    if redis_client:
                        await redis_client.execute_command('MEMORY', 'PURGE')
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")
                await asyncio.sleep(60)

class CacheInvalidationManager:
    """Manage cache invalidation with tags and patterns"""
    
    def __init__(self):
        self.tag_prefix = "cache_tag:"
        
    async def add_tags(self, cache_key: str, tags: List[str], ttl: int):
        """Add invalidation tags for a cache key"""
        
        try:
            redis_client = redis_cluster.current_master
            if not redis_client:
                return
            
            # Store tags for this key
            for tag in tags:
                tag_key = f"{self.tag_prefix}{tag}"
                await redis_client.sadd(tag_key, cache_key)
                await redis_client.expire(tag_key, ttl + 3600)  # Tags live longer
                
        except Exception as e:
            logger.error(f"Failed to add tags for key {cache_key}: {e}")
    
    async def invalidate_by_tags(self, tags: List[str]) -> int:
        """Invalidate all cache entries with specified tags"""
        
        try:
            redis_client = redis_cluster.current_master
            if not redis_client:
                return 0
            
            keys_to_delete = set()
            
            # Collect all keys with these tags
            for tag in tags:
                tag_key = f"{self.tag_prefix}{tag}"
                tagged_keys = await redis_client.smembers(tag_key)
                keys_to_delete.update(tagged_keys)
                
                # Delete the tag set itself
                await redis_client.delete(tag_key)
            
            # Delete all collected keys
            if keys_to_delete:
                deleted_count = await redis_client.delete(*keys_to_delete)
                logger.info(f"Invalidated {deleted_count} cache entries for tags: {tags}")
                return deleted_count
            
            return 0
            
        except Exception as e:
            logger.error(f"Cache invalidation failed for tags {tags}: {e}")
            return 0
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching a pattern"""
        
        try:
            redis_client = redis_cluster.current_master
            if not redis_client:
                return 0
            
            keys_to_delete = []
            async for key in redis_client.scan_iter(match=pattern):
                keys_to_delete.append(key)
            
            if keys_to_delete:
                deleted_count = await redis_client.delete(*keys_to_delete)
                logger.info(f"Invalidated {deleted_count} cache entries for pattern: {pattern}")
                return deleted_count
            
            return 0
            
        except Exception as e:
            logger.error(f"Pattern invalidation failed for {pattern}: {e}")
            return 0

    async def optimize_memory_usage(self) -> Dict[str, int]:
        """Optimize Redis memory usage"""
        
        try:
            redis_client = redis_cluster.current_master
            if not redis_client:
                return {'status': 'unavailable'}
            
            optimization_results = {
                'expired_keys_removed': 0,
                'large_keys_compressed': 0,
                'fragmented_keys_defragmented': 0
            }
            
            # 1. Remove expired keys
            optimization_results['expired_keys_removed'] = await self.cleanup_expired_keys()
            
            # 2. Compress large values
            large_key_count = 0
            async for key in redis_client.scan_iter(match="*", count=500):
                try:
                    memory_usage = await redis_client.memory_usage(key)
                    if memory_usage and memory_usage > 1024 * 1024:  # > 1MB
                        # Get value and compress if it's JSON
                        value = await redis_client.get(key)
                        if value and len(value) > 10000:  # Large string
                            try:
                                # Try to compress JSON data
                                import gzip
                                import base64
                                
                                compressed = gzip.compress(value.encode('utf-8'))
                                if len(compressed) < len(value) * 0.7:  # 30% compression
                                    compressed_b64 = base64.b64encode(compressed).decode('utf-8')
                                    ttl = await redis_client.ttl(key)
                                    
                                    # Store compressed version with marker
                                    compressed_key = f"compressed:{key}"
                                    await redis_client.setex(compressed_key, ttl if ttl > 0 else 3600, compressed_b64)
                                    await redis_client.delete(key)
                                    
                                    large_key_count += 1
                                    
                            except Exception:
                                pass  # Skip compression if it fails
                        
                        # Limit processing to avoid blocking
                        if large_key_count >= 10:
                            break
                            
                except Exception:
                    continue
            
            optimization_results['large_keys_compressed'] = large_key_count
            
            # 3. Memory defragmentation
            try:
                await redis_client.execute_command('MEMORY', 'PURGE')
                optimization_results['fragmented_keys_defragmented'] = 1
            except Exception:
                pass
            
            return optimization_results
            
        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            return {'error': str(e)}

class CacheInvalidationManager:
    """Advanced cache invalidation with tags, patterns, and dependencies"""
    
    def __init__(self):
        self.tag_prefix = "cache_tag:"
        self.dependency_prefix = "cache_dep:"
        self.invalidation_log_prefix = "inv_log:"
        
    async def add_tags(self, cache_key: str, tags: List[str], ttl: int):
        """Add invalidation tags for a cache key with dependency tracking"""
        
        try:
            redis_client = redis_cluster.current_master
            if not redis_client:
                return
            
            # Use pipeline for atomic operations
            async with redis_client.pipeline() as pipe:
                # Store tags for this key
                for tag in tags:
                    tag_key = f"{self.tag_prefix}{tag}"
                    await pipe.sadd(tag_key, cache_key)
                    await pipe.expire(tag_key, ttl + 3600)  # Tags live longer
                
                # Store reverse mapping (key -> tags)
                key_tags_key = f"{self.dependency_prefix}{cache_key}"
                await pipe.sadd(key_tags_key, *tags)
                await pipe.expire(key_tags_key, ttl + 3600)
                
                # Log cache creation
                log_key = f"{self.invalidation_log_prefix}{int(time.time())}"
                log_data = {
                    'action': 'cache_set',
                    'key': cache_key,
                    'tags': tags,
                    'timestamp': time.time()
                }
                await pipe.setex(log_key, 86400, json.dumps(log_data))  # 24h log retention
                
                await pipe.execute()
                
        except Exception as e:
            logger.error(f"Failed to add tags for key {cache_key}: {e}")
    
    async def invalidate_by_tags(self, tags: List[str]) -> int:
        """Invalidate all cache entries with specified tags"""
        
        try:
            redis_client = redis_cluster.current_master
            if not redis_client:
                return 0
            
            keys_to_delete = set()
            tag_keys_to_delete = []
            
            # Collect all keys with these tags
            for tag in tags:
                tag_key = f"{self.tag_prefix}{tag}"
                tagged_keys = await redis_client.smembers(tag_key)
                keys_to_delete.update(tagged_keys)
                tag_keys_to_delete.append(tag_key)
            
            # Also collect dependency keys
            dependency_keys_to_delete = []
            for key in keys_to_delete:
                dep_key = f"{self.dependency_prefix}{key}"
                dependency_keys_to_delete.append(dep_key)
            
            # Delete everything in batches
            total_deleted = 0
            
            if keys_to_delete:
                # Delete cache keys in batches of 100
                keys_list = list(keys_to_delete)
                for i in range(0, len(keys_list), 100):
                    batch = keys_list[i:i+100]
                    deleted = await redis_client.delete(*batch)
                    total_deleted += deleted
            
            # Delete tag keys
            if tag_keys_to_delete:
                await redis_client.delete(*tag_keys_to_delete)
            
            # Delete dependency keys
            if dependency_keys_to_delete:
                await redis_client.delete(*dependency_keys_to_delete)
            
            # Log invalidation
            log_key = f"{self.invalidation_log_prefix}{int(time.time())}"
            log_data = {
                'action': 'invalidate_by_tags',
                'tags': tags,
                'keys_deleted': total_deleted,
                'timestamp': time.time()
            }
            await redis_client.setex(log_key, 86400, json.dumps(log_data))
            
            logger.info(f"Invalidated {total_deleted} cache entries for tags: {tags}")
            return total_deleted
            
        except Exception as e:
            logger.error(f"Cache invalidation failed for tags {tags}: {e}")
            return 0
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching a pattern with batching"""
        
        try:
            redis_client = redis_cluster.current_master
            if not redis_client:
                return 0
            
            keys_to_delete = []
            total_deleted = 0
            
            # Collect keys in batches to avoid memory issues
            async for key in redis_client.scan_iter(match=pattern, count=1000):
                keys_to_delete.append(key)
                
                # Process in batches of 500
                if len(keys_to_delete) >= 500:
                    deleted = await redis_client.delete(*keys_to_delete)
                    total_deleted += deleted
                    logger.info(f"Batch deleted {deleted} keys for pattern {pattern}")
                    keys_to_delete = []
            
            # Delete remaining keys
            if keys_to_delete:
                deleted = await redis_client.delete(*keys_to_delete)
                total_deleted += deleted
            
            # Log pattern invalidation
            log_key = f"{self.invalidation_log_prefix}{int(time.time())}"
            log_data = {
                'action': 'invalidate_pattern',
                'pattern': pattern,
                'keys_deleted': total_deleted,
                'timestamp': time.time()
            }
            await redis_client.setex(log_key, 86400, json.dumps(log_data))
            
            logger.info(f"Invalidated {total_deleted} cache entries for pattern: {pattern}")
            return total_deleted
            
        except Exception as e:
            logger.error(f"Pattern invalidation failed for {pattern}: {e}")
            return 0

# Global instances
redis_cluster = RedisClusterManager()
memory_monitor = RedisMemoryMonitor()
cache_invalidator = CacheInvalidationManager()

# Background monitoring tasks
async def start_redis_monitoring():
    """Start background Redis monitoring tasks"""
    
    # Start memory monitoring
    asyncio.create_task(memory_monitor.monitor_memory_usage())
    
    # Start periodic cleanup
    asyncio.create_task(periodic_cache_cleanup())
    
    logger.info("Redis monitoring tasks started")

async def periodic_cache_cleanup():
    """Periodic cleanup of cache data"""
    
    while True:
        try:
            # Memory optimization every 30 minutes
            optimization_results = await memory_monitor.optimize_memory_usage()
            logger.info(f"Memory optimization completed: {optimization_results}")
            
            # Wait 30 minutes
            await asyncio.sleep(1800)
            
        except Exception as e:
            logger.error(f"Periodic cleanup error: {e}")
            await asyncio.sleep(300)  # Retry after 5 minutes on error