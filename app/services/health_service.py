import asyncio
import time
import sys
import platform
from typing import Dict, Any
from app.repositories.health_repository import HealthRepository
from app.services.redis_service import redis_service
from app.core.config import settings
from app.core.circuit_breaker import database_circuit_breaker, redis_circuit_breaker
import logging

logger = logging.getLogger(__name__)

class HealthService:
    """Health check service for dependencies"""
    
    async def check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            with HealthRepository() as repo:
                connection_check = repo.check_database_connection()
                
                if connection_check['status'] == 'healthy':
                    # Additional checks if connection is healthy
                    icd10_count = repo.get_icd10_count()
                    icd11_count = repo.get_icd11_count()
                    db_size = repo.get_database_size()
                    indexes = repo.check_indexes_exist()
                    
                    connection_check.update({
                        'details': 'Database connection and data checks successful',
                        'icd10_count': icd10_count,
                        'icd11_count': icd11_count,
                        'total_codes': icd10_count + icd11_count,
                        'database_size': db_size,
                        'indexes_status': indexes
                    })
                
                return connection_check
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "response_time_ms": 0,
                "details": f"Database health check error: {str(e)}"
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """Comprehensive Redis health check with performance metrics"""
        start_time = time.time()
        
        try:
            # Ensure Redis connection
            await redis_service._ensure_connected()
            
            if not redis_service.redis_client:
                return {
                    "status": "unhealthy",
                    "response_time_ms": 0,
                    "details": "Redis client not initialized",
                    "connection_pool": "unavailable"
                }
            
            # Test Redis operations
            test_key = "health_check_test"
            test_value = {"timestamp": time.time(), "test": True}
            
            # Test SET operation
            set_success = await redis_service.set(test_key, test_value, ttl=60)
            
            # Test GET operation
            get_result = await redis_service.get(test_key)
            
            # Test DELETE operation
            delete_success = await redis_service.delete(test_key)
            
            # Get Redis stats
            redis_stats = await redis_service.get_stats()
            
            response_time = round((time.time() - start_time) * 1000, 2)
            
            # Determine health status
            operations_successful = set_success and get_result and delete_success
            status = "healthy" if operations_successful and redis_stats.get('connected') else "degraded"
            
            return {
                "status": status,
                "response_time_ms": response_time,
                "details": "Redis operations completed successfully" if operations_successful else "Some Redis operations failed",
                "operations": {
                    "set": set_success,
                    "get": bool(get_result),
                    "delete": delete_success
                },
                "connection_pool": {
                    "status": "active" if redis_service.connection_pool else "inactive",
                    "max_connections": 20
                },
                "performance": redis_stats
            }
            
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "details": f"Redis health check error: {str(e)}",
                "error": str(e)
            }
    
    async def check_data_integrity(self) -> Dict[str, Any]:
        """Check data integrity and counts"""
        try:
            with HealthRepository() as repo:
                # Check table existence
                icd10_exists = repo.check_table_exists('icd10_codes')
                icd11_exists = repo.check_table_exists('icd11_codes')
                
                if not icd10_exists or not icd11_exists:
                    return {
                        "status": "unhealthy",
                        "details": "Required tables missing",
                        "icd10_table_exists": icd10_exists,
                        "icd11_table_exists": icd11_exists
                    }
                
                # Get counts
                icd10_count = repo.get_icd10_count()
                icd11_count = repo.get_icd11_count()
                total_codes = icd10_count + icd11_count
                
                # Check indexes
                indexes = repo.check_indexes_exist()
                all_indexes_exist = all(indexes.values()) if indexes else False
                
                # Determine health status
                is_healthy = (
                    total_codes > 70000 and  # Expected minimum codes
                    icd10_count > 60000 and  # Minimum ICD-10 codes
                    all_indexes_exist  # All required indexes exist
                )
                
                status = "healthy" if is_healthy else "degraded" if total_codes > 0 else "unhealthy"
                
                return {
                    "status": status,
                    "icd10_codes": icd10_count,
                    "icd11_codes": icd11_count,
                    "total_codes": total_codes,
                    "indexes_status": indexes,
                    "all_indexes_exist": all_indexes_exist,
                    "details": f"Data integrity check: {total_codes} total codes, indexes: {'OK' if all_indexes_exist else 'Missing'}"
                }
        except Exception as e:
            logger.error(f"Data integrity check failed: {e}")
            return {
                "status": "unhealthy",
                "details": f"Data integrity check failed: {str(e)}"
            }
    
    async def get_comprehensive_health(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        start_time = time.time()
        
        # Run all health checks concurrently with timeout
        try:
            db_health, redis_health, data_health = await asyncio.wait_for(
                asyncio.gather(
                    self.check_database(),
                    self.check_redis(), 
                    self.check_data_integrity(),
                    return_exceptions=True
                ),
                timeout=30.0  # 30 second timeout
            )
        except asyncio.TimeoutError:
            logger.error("Health check timeout after 30 seconds")
            return {
                "status": "unhealthy",
                "timestamp": time.time(),
                "response_time_ms": 30000,
                "version": settings.app_version,
                "error": "Health check timeout",
                "dependencies": {
                    "database": {"status": "timeout"},
                    "redis": {"status": "timeout"},
                    "data": {"status": "timeout"}
                }
            }
        
        # Handle exceptions with detailed error info
        if isinstance(db_health, Exception):
            logger.error(f"Database health check exception: {db_health}")
            db_health = {
                "status": "unhealthy", 
                "details": f"Database health check failed: {str(db_health)}",
                "error_type": type(db_health).__name__
            }
        if isinstance(redis_health, Exception):
            logger.error(f"Redis health check exception: {redis_health}")
            redis_health = {
                "status": "unhealthy", 
                "details": f"Redis health check failed: {str(redis_health)}",
                "error_type": type(redis_health).__name__
            }
        if isinstance(data_health, Exception):
            logger.error(f"Data health check exception: {data_health}")
            data_health = {
                "status": "unhealthy", 
                "details": f"Data integrity check failed: {str(data_health)}",
                "error_type": type(data_health).__name__
            }
        
        # Determine overall status
        all_statuses = [db_health["status"], redis_health["status"], data_health["status"]]
        
        if all(status == "healthy" for status in all_statuses):
            overall_status = "healthy"
        elif any(status == "unhealthy" for status in all_statuses):
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"
        
        total_time = round((time.time() - start_time) * 1000, 2)
        
        # Calculate service uptime and additional metrics
        uptime_seconds = time.time() - getattr(self, '_start_time', time.time())
        
        return {
            "status": overall_status,
            "timestamp": time.time(),
            "response_time_ms": total_time,
            "version": settings.app_version,
            "uptime_seconds": round(uptime_seconds, 2),
            "environment": getattr(settings, 'environment', 'development'),
            "host": settings.host,
            "port": settings.port,
            "dependencies": {
                "database": db_health,
                "redis": redis_health,
                "data": data_health
            },
            "system_info": {
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "platform": platform.system(),
                "architecture": platform.machine()
            },
            "circuit_breakers": {
                "database": {
                    "state": database_circuit_breaker.state.value,
                    "failure_count": database_circuit_breaker.failure_count
                },
                "redis": {
                    "state": redis_circuit_breaker.state.value,
                    "failure_count": redis_circuit_breaker.failure_count
                }
            }
        }

# Global health service instance
health_service = HealthService()