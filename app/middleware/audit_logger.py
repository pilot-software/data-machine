"""
API Call Auditing Middleware
Logs every API call for analytics and billing
"""
from fastapi import Request
from sqlalchemy import text
from app.db.database import SessionLocal
import time
import json

async def audit_middleware(request: Request, call_next):
    """Log all API calls"""
    start_time = time.time()
    
    # Get request details
    api_key = request.headers.get("X-API-Key", "anonymous")
    endpoint = request.url.path
    method = request.method
    query_params = str(request.query_params)
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "unknown")
    
    # Process request
    response = await call_next(request)
    
    # Calculate response time
    response_time_ms = (time.time() - start_time) * 1000
    
    # Log to database (async, don't block response)
    try:
        db = SessionLocal()
        sql = text("""
            INSERT INTO api_call_logs 
            (api_key, endpoint, method, query_params, response_status, 
             response_time_ms, ip_address, user_agent)
            VALUES (:api_key, :endpoint, :method, :query_params, :status, 
                    :response_time, :ip, :user_agent)
        """)
        
        db.execute(sql, {
            "api_key": api_key[:50],  # Truncate for security
            "endpoint": endpoint,
            "method": method,
            "query_params": query_params[:500],  # Limit size
            "status": response.status_code,
            "response_time": response_time_ms,
            "ip": ip_address,
            "user_agent": user_agent[:200]
        })
        db.commit()
        db.close()
    except Exception as e:
        # Don't fail request if logging fails
        print(f"Audit logging error: {e}")
    
    return response

def log_search(api_key: str, query: str, endpoint: str, results_count: int, response_time_ms: float):
    """Log search queries specifically"""
    try:
        db = SessionLocal()
        sql = text("""
            INSERT INTO search_logs 
            (api_key, query, endpoint, results_count, response_time_ms)
            VALUES (:api_key, :query, :endpoint, :results, :response_time)
        """)
        
        db.execute(sql, {
            "api_key": api_key[:50],
            "query": query[:200],
            "endpoint": endpoint,
            "results": results_count,
            "response_time": response_time_ms
        })
        db.commit()
        db.close()
    except Exception as e:
        print(f"Search logging error: {e}")
