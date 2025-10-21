"""Service factory for dependency injection setup"""

from app.core.dependencies import container, ITerminologyRepository, ICacheService
from app.repositories.async_icd10_repository import AsyncICD10Repository
from app.services.cache_service import RedisCacheService, InMemoryCacheService
from app.core.settings import settings
import redis.asyncio as aioredis
import logging

logger = logging.getLogger(__name__)

async def setup_dependencies():
    """Setup all service dependencies"""
    
    # Setup cache service
    try:
        if settings.redis.host:
            redis_client = await aioredis.from_url(
                f"redis://{settings.redis.host}:{settings.redis.port}",
                password=settings.redis.password,
                decode_responses=True
            )
            cache_service = RedisCacheService(redis_client)
            logger.info("Using Redis cache service")
        else:
            cache_service = InMemoryCacheService()
            logger.info("Using in-memory cache service")
    except Exception as e:
        logger.warning(f"Redis connection failed, using in-memory cache: {e}")
        cache_service = InMemoryCacheService()
    
    # Register services
    container.register_singleton(ICacheService, cache_service)
    
    # Repository factory (creates new instance per request)
    def repository_factory():
        return AsyncICD10Repository(None)  # Session injected later
    
    container.register_factory(ITerminologyRepository, repository_factory)
    
    logger.info("Dependency injection container configured")

def get_cache_service() -> ICacheService:
    """Get cache service instance"""
    return container.get(ICacheService)

def get_repository() -> ITerminologyRepository:
    """Get repository instance"""
    return container.get(ITerminologyRepository)