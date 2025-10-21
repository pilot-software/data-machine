"""Legacy config - use app.core.settings instead"""

from .settings import settings

# Backward compatibility
class Settings:
    def __init__(self):
        self.DATABASE_URL = settings.database.url
        self.HOST = settings.api.host
        self.PORT = settings.api.port
        self.DEBUG = settings.api.debug
        self.CACHE_TTL = settings.cache.ttl
        self.MAX_SUGGESTIONS = 10
        self.CORS_ORIGINS = settings.api.cors_origins
        self.DB_POOL_SIZE = settings.database.pool_size
        self.DB_MAX_OVERFLOW = settings.database.max_overflow
        
        # Legacy properties
        self.app_name = "HMS Terminology Service"
        self.redis_host = settings.redis.host
        self.redis_port = settings.redis.port
        self.database_url = settings.database.url