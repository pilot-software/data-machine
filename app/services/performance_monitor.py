import time
import psutil
import logging
from typing import Dict, Any
from app.services.redis_service import redis_service

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Enterprise performance monitoring and metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
    
    def record_request(self, endpoint: str, duration_ms: float, success: bool = True):
        """Record API request metrics"""
        self.request_count += 1
        if not success:
            self.error_count += 1
        
        # Store in Redis for analytics
        metrics_key = f"metrics:requests:{int(time.time() // 60)}"  # Per minute
        redis_service.increment(metrics_key)
        redis_service.expire(metrics_key, 3600)  # Keep for 1 hour
        
        # Store endpoint-specific metrics
        endpoint_key = f"metrics:endpoint:{endpoint}:{int(time.time() // 60)}"
        redis_service.increment(endpoint_key)
        redis_service.expire(endpoint_key, 3600)
        
        # Store response times
        time_key = f"metrics:response_time:{endpoint}"
        redis_service.add_to_list(time_key, duration_ms, max_length=100)
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system performance metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_usage_percent': cpu_percent,
                'memory': {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'used_percent': memory.percent
                },
                'disk': {
                    'total_gb': round(disk.total / (1024**3), 2),
                    'free_gb': round(disk.free / (1024**3), 2),
                    'used_percent': round((disk.used / disk.total) * 100, 2)
                },
                'uptime_hours': round((time.time() - self.start_time) / 3600, 2)
            }
        except Exception as e:
            logger.error(f"System metrics error: {e}")
            return {'error': str(e)}
    
    def get_api_metrics(self) -> Dict[str, Any]:
        """Get API performance metrics"""
        try:
            current_minute = int(time.time() // 60)
            
            # Get requests per minute for last 10 minutes
            rpm_data = []
            for i in range(10):
                minute_key = f"metrics:requests:{current_minute - i}"
                count = redis_service.get(minute_key) or 0
                rpm_data.append({
                    'minute': current_minute - i,
                    'requests': int(count)
                })
            
            # Calculate averages
            total_requests = sum(item['requests'] for item in rpm_data)
            avg_rpm = total_requests / 10 if total_requests > 0 else 0
            
            return {
                'total_requests': self.request_count,
                'total_errors': self.error_count,
                'error_rate_percent': round((self.error_count / max(self.request_count, 1)) * 100, 2),
                'requests_per_minute': rpm_data,
                'average_rpm': round(avg_rpm, 2),
                'cache_hit_rate': self.get_cache_metrics()
            }
        except Exception as e:
            logger.error(f"API metrics error: {e}")
            return {'error': str(e)}
    
    def get_cache_metrics(self) -> Dict[str, Any]:
        """Get Redis cache performance metrics"""
        try:
            info = redis_service.redis_client.info()
            
            return {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_mb': round(info.get('used_memory', 0) / (1024*1024), 2),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate_percent': self.calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                )
            }
        except Exception as e:
            logger.error(f"Cache metrics error: {e}")
            return {'error': str(e)}
    
    def calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)
    
    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        try:
            # Test database connection
            from app.db.database import SessionLocal
            db_healthy = True
            try:
                db = SessionLocal()
                db.execute("SELECT 1")
                db.close()
            except Exception:
                db_healthy = False
            
            # Test Redis connection
            redis_healthy = redis_service.ping()
            
            # Get system load
            system_metrics = self.get_system_metrics()
            
            # Determine overall health
            overall_healthy = (
                db_healthy and 
                redis_healthy and 
                system_metrics.get('cpu_usage_percent', 100) < 90 and
                system_metrics.get('memory', {}).get('used_percent', 100) < 90
            )
            
            return {
                'status': 'healthy' if overall_healthy else 'degraded',
                'timestamp': time.time(),
                'components': {
                    'database': 'healthy' if db_healthy else 'unhealthy',
                    'redis': 'healthy' if redis_healthy else 'unhealthy',
                    'system_load': 'normal' if system_metrics.get('cpu_usage_percent', 0) < 80 else 'high'
                },
                'metrics': {
                    'uptime_hours': round((time.time() - self.start_time) / 3600, 2),
                    'total_requests': self.request_count,
                    'error_rate': round((self.error_count / max(self.request_count, 1)) * 100, 2)
                }
            }
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': time.time()
            }


# Global performance monitor
performance_monitor = PerformanceMonitor()