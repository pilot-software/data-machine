from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import time
import asyncio
from typing import Dict, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class RateLimitTier(Enum):
    """Rate limit tiers for different user types"""
    ANONYMOUS = "anonymous"
    AUTHENTICATED = "authenticated"
    PREMIUM = "premium"
    ADMIN = "admin"

class AdvancedRateLimiter:
    """Advanced rate limiter with multiple algorithms and tiers"""
    
    def __init__(self):
        # Sliding window counters
        self.sliding_windows: Dict[str, Dict[str, list]] = {}
        
        # Token bucket for burst handling
        self.token_buckets: Dict[str, Dict[str, float]] = {}
        
        # Rate limit configurations by tier
        self.rate_limits = {
            RateLimitTier.ANONYMOUS: {
                'requests_per_minute': 1000,
                'requests_per_hour': 10000,
                'burst_capacity': 100,
                'token_refill_rate': 10.0  # tokens per second
            },
            RateLimitTier.AUTHENTICATED: {
                'requests_per_minute': 200,
                'requests_per_hour': 5000,
                'burst_capacity': 50,
                'token_refill_rate': 3.0
            },
            RateLimitTier.PREMIUM: {
                'requests_per_minute': 1000,
                'requests_per_hour': 20000,
                'burst_capacity': 200,
                'token_refill_rate': 10.0
            },
            RateLimitTier.ADMIN: {
                'requests_per_minute': 10000,
                'requests_per_hour': 100000,
                'burst_capacity': 1000,
                'token_refill_rate': 50.0
            }
        }
        
        # Request timeout configurations
        self.timeout_configs = {
            '/api/v1/search': 30.0,
            '/api/v1/enterprise': 60.0,
            '/api/v1/health': 10.0,
            'default': 30.0
        }
    
    def _get_client_identifier(self, request: Request) -> Tuple[str, RateLimitTier]:
        """Get client identifier and determine rate limit tier"""
        
        # Check for API key in headers
        api_key = request.headers.get('X-API-Key')
        if api_key:
            # In production, validate API key against database
            if api_key.startswith('admin_'):
                return f"api_key:{api_key}", RateLimitTier.ADMIN
            elif api_key.startswith('premium_'):
                return f"api_key:{api_key}", RateLimitTier.PREMIUM
            else:
                return f"api_key:{api_key}", RateLimitTier.AUTHENTICATED
        
        # Check for JWT token
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
            # In production, decode and validate JWT
            return f"jwt:{token[:20]}", RateLimitTier.AUTHENTICATED
        
        # Fall back to IP address for anonymous users
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}", RateLimitTier.ANONYMOUS
    
    def _sliding_window_check(self, client_id: str, tier: RateLimitTier, current_time: float) -> bool:
        """Sliding window rate limit check"""
        
        if client_id not in self.sliding_windows:
            self.sliding_windows[client_id] = {'minute': [], 'hour': []}
        
        windows = self.sliding_windows[client_id]
        limits = self.rate_limits[tier]
        
        # Clean old requests
        windows['minute'] = [t for t in windows['minute'] if current_time - t < 60]
        windows['hour'] = [t for t in windows['hour'] if current_time - t < 3600]
        
        # Check limits
        if len(windows['minute']) >= limits['requests_per_minute']:
            return False
        if len(windows['hour']) >= limits['requests_per_hour']:
            return False
        
        # Add current request
        windows['minute'].append(current_time)
        windows['hour'].append(current_time)
        
        return True
    
    def _token_bucket_check(self, client_id: str, tier: RateLimitTier, current_time: float) -> bool:
        """Token bucket algorithm for burst handling"""
        
        if client_id not in self.token_buckets:
            self.token_buckets[client_id] = {
                'tokens': self.rate_limits[tier]['burst_capacity'],
                'last_refill': current_time
            }
        
        bucket = self.token_buckets[client_id]
        limits = self.rate_limits[tier]
        
        # Refill tokens based on time elapsed
        time_elapsed = current_time - bucket['last_refill']
        tokens_to_add = time_elapsed * limits['token_refill_rate']
        
        bucket['tokens'] = min(
            limits['burst_capacity'],
            bucket['tokens'] + tokens_to_add
        )
        bucket['last_refill'] = current_time
        
        # Check if we have tokens available
        if bucket['tokens'] >= 1.0:
            bucket['tokens'] -= 1.0
            return True
        
        return False
    
    async def check_rate_limit(self, request: Request) -> Tuple[bool, Dict[str, any]]:
        """Comprehensive rate limit check"""
        
        client_id, tier = self._get_client_identifier(request)
        current_time = time.time()
        
        # Apply both sliding window and token bucket
        sliding_window_ok = self._sliding_window_check(client_id, tier, current_time)
        token_bucket_ok = self._token_bucket_check(client_id, tier, current_time)
        
        # Request is allowed if both checks pass
        allowed = sliding_window_ok and token_bucket_ok
        
        # Calculate retry after time
        retry_after = 60 if not sliding_window_ok else 1
        
        # Get current usage stats
        windows = self.sliding_windows.get(client_id, {'minute': [], 'hour': []})
        bucket = self.token_buckets.get(client_id, {'tokens': 0})
        limits = self.rate_limits[tier]
        
        rate_limit_info = {
            'allowed': allowed,
            'tier': tier.value,
            'retry_after': retry_after,
            'usage': {
                'requests_this_minute': len(windows['minute']),
                'requests_this_hour': len(windows['hour']),
                'available_tokens': int(bucket['tokens']),
                'burst_capacity': limits['burst_capacity']
            },
            'limits': {
                'per_minute': limits['requests_per_minute'],
                'per_hour': limits['requests_per_hour']
            }
        }
        
        return allowed, rate_limit_info
    
    def get_timeout_for_path(self, path: str) -> float:
        """Get request timeout for specific path"""
        
        for pattern, timeout in self.timeout_configs.items():
            if pattern != 'default' and path.startswith(pattern):
                return timeout
        
        return self.timeout_configs['default']
    
    async def cleanup_old_data(self):
        """Periodic cleanup of old rate limit data"""
        
        current_time = time.time()
        
        # Clean sliding windows
        for client_id in list(self.sliding_windows.keys()):
            windows = self.sliding_windows[client_id]
            windows['minute'] = [t for t in windows['minute'] if current_time - t < 60]
            windows['hour'] = [t for t in windows['hour'] if current_time - t < 3600]
            
            # Remove empty entries
            if not windows['minute'] and not windows['hour']:
                del self.sliding_windows[client_id]
        
        # Clean token buckets (remove inactive clients)
        for client_id in list(self.token_buckets.keys()):
            bucket = self.token_buckets[client_id]
            if current_time - bucket['last_refill'] > 3600:  # 1 hour inactive
                del self.token_buckets[client_id]
        
        logger.info(f"Rate limiter cleanup: {len(self.sliding_windows)} active clients")

class RequestTimeoutManager:
    """Manage request timeouts and resource limits"""
    
    def __init__(self):
        self.active_requests: Dict[str, float] = {}
        self.max_concurrent_requests = 1000
        self.current_request_count = 0
    
    async def acquire_request_slot(self, request_id: str) -> bool:
        """Acquire a request processing slot"""
        
        if self.current_request_count >= self.max_concurrent_requests:
            return False
        
        self.active_requests[request_id] = time.time()
        self.current_request_count += 1
        return True
    
    async def release_request_slot(self, request_id: str):
        """Release a request processing slot"""
        
        if request_id in self.active_requests:
            del self.active_requests[request_id]
            self.current_request_count = max(0, self.current_request_count - 1)
    
    async def check_request_timeout(self, request_id: str, timeout: float) -> bool:
        """Check if request has timed out"""
        
        if request_id not in self.active_requests:
            return False
        
        elapsed = time.time() - self.active_requests[request_id]
        return elapsed > timeout
    
    def get_resource_stats(self) -> Dict[str, any]:
        """Get current resource usage statistics"""
        
        return {
            'active_requests': self.current_request_count,
            'max_concurrent_requests': self.max_concurrent_requests,
            'utilization_percentage': (self.current_request_count / self.max_concurrent_requests) * 100,
            'oldest_request_age': min(
                [time.time() - start_time for start_time in self.active_requests.values()],
                default=0
            )
        }

# Global instances
advanced_rate_limiter = AdvancedRateLimiter()
timeout_manager = RequestTimeoutManager()

async def advanced_rate_limit_middleware(request: Request, call_next):
    """Advanced rate limiting and resource management middleware"""
    
    # Skip rate limiting for health checks
    if request.url.path.startswith("/api/v1/health"):
        return await call_next(request)
    
    # Generate unique request ID
    request_id = f"{id(request)}_{time.time()}"
    
    try:
        # Check rate limits
        allowed, rate_info = await advanced_rate_limiter.check_rate_limit(request)
        
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "tier": rate_info['tier'],
                    "retry_after": rate_info['retry_after'],
                    "usage": rate_info['usage'],
                    "limits": rate_info['limits']
                },
                headers={
                    "X-RateLimit-Limit": str(rate_info['limits']['per_minute']),
                    "X-RateLimit-Remaining": str(max(0, rate_info['limits']['per_minute'] - rate_info['usage']['requests_this_minute'])),
                    "X-RateLimit-Reset": str(int(time.time() + 60)),
                    "Retry-After": str(rate_info['retry_after'])
                }
            )
        
        # Acquire request processing slot
        if not await timeout_manager.acquire_request_slot(request_id):
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Service temporarily overloaded",
                    "message": "Too many concurrent requests. Please try again later."
                }
            )
        
        # Get timeout for this path
        timeout = advanced_rate_limiter.get_timeout_for_path(request.url.path)
        
        # Process request with timeout
        try:
            response = await asyncio.wait_for(
                call_next(request),
                timeout=timeout
            )
            
            # Add rate limit headers to response
            response.headers["X-RateLimit-Limit"] = str(rate_info['limits']['per_minute'])
            response.headers["X-RateLimit-Remaining"] = str(max(0, rate_info['limits']['per_minute'] - rate_info['usage']['requests_this_minute']))
            response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))
            
            return response
            
        except asyncio.TimeoutError:
            logger.warning(f"Request timeout after {timeout}s for path {request.url.path}")
            return JSONResponse(
                status_code=408,
                content={
                    "error": "Request timeout",
                    "message": f"Request exceeded {timeout} second timeout limit"
                }
            )
    
    finally:
        # Always release the request slot
        await timeout_manager.release_request_slot(request_id)

# Periodic cleanup task
async def rate_limiter_cleanup_task():
    """Background task to clean up rate limiter data"""
    while True:
        try:
            await advanced_rate_limiter.cleanup_old_data()
            await asyncio.sleep(300)  # Clean up every 5 minutes
        except Exception as e:
            logger.error(f"Rate limiter cleanup error: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute on error