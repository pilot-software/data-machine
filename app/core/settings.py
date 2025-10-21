"""Centralized configuration management with validation"""

from pydantic_settings import BaseSettings
from pydantic import validator, Field
from typing import Optional, List
import os

class Settings(BaseSettings):
    """Centralized application settings"""
    
    # App
    app_name: str = Field('HMS Terminology Service', env='APP_NAME')
    app_version: str = Field('1.0.0', env='APP_VERSION')
    
    # Database
    database_url: str = Field(..., env='DATABASE_URL')
    db_pool_size: int = Field(10, env='DB_POOL_SIZE')
    db_max_overflow: int = Field(20, env='DB_MAX_OVERFLOW')
    
    # Redis
    redis_host: str = Field('localhost', env='REDIS_HOST')
    redis_port: int = Field(6379, env='REDIS_PORT')
    redis_db: int = Field(0, env='REDIS_DB')
    redis_password: Optional[str] = Field(None, env='REDIS_PASSWORD')
    redis_ttl: int = Field(3600, env='REDIS_TTL')
    
    # API
    host: str = Field('0.0.0.0', env='HOST')
    port: int = Field(8001, env='PORT')
    debug: bool = Field(False, env='DEBUG')
    
    # Logging
    log_level: str = Field('INFO', env='LOG_LEVEL')
    log_file: str = Field('logs/app.log', env='LOG_FILE')
    
    # Cache
    cache_ttl: int = Field(3600, env='CACHE_TTL')
    cache_max_size: int = Field(1000, env='CACHE_MAX_SIZE')
    
    # Performance
    max_suggestions: int = Field(10, env='MAX_SUGGESTIONS')
    fuzzy_threshold: float = Field(0.6, env='FUZZY_THRESHOLD')
    
    # Rate Limiting
    rate_limit_default: int = Field(100, env='RATE_LIMIT_DEFAULT')
    rate_limit_premium: int = Field(1000, env='RATE_LIMIT_PREMIUM')
    
    model_config = {'env_file': '.env', 'case_sensitive': False, 'extra': 'ignore'}

# Global settings instance
_settings = Settings()

# Backward compatibility wrapper
class SettingsWrapper:
    def __init__(self, s):
        self._s = s
        
    def __getattr__(self, name):
        return getattr(self._s, name)
    
    @property
    def database(self):
        class DB:
            url = self._s.database_url
            pool_size = self._s.db_pool_size
            max_overflow = self._s.db_max_overflow
        return DB()
    
    @property
    def redis(self):
        class Redis:
            host = self._s.redis_host
            port = self._s.redis_port
            password = self._s.redis_password
        return Redis()
    
    @property
    def api(self):
        class API:
            host = self._s.host
            port = self._s.port
            debug = self._s.debug
            cors_origins = ['*']
        return API()
    
    @property
    def cache(self):
        class Cache:
            ttl = self._s.cache_ttl
            max_size = self._s.cache_max_size
        return Cache()

settings = SettingsWrapper(_settings)
