"""
Internal Analytics Endpoints (Admin Only) - Using Audit Logs
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from app.db.database import SessionLocal
from app.middleware.auth import verify_api_key

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"], dependencies=[Depends(verify_api_key)])

@router.get("/usage/summary")
async def get_usage_summary(days: int = Query(30, description="Number of days")):
    """Get overall API usage summary from audit logs"""
    db = SessionLocal()
    try:
        sql = text("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as total_calls,
                COUNT(DISTINCT api_key) as unique_users,
                AVG(response_time_ms) as avg_response_time,
                SUM(CASE WHEN response_status >= 200 AND response_status < 300 THEN 1 ELSE 0 END) as successful_calls,
                SUM(CASE WHEN response_status >= 400 THEN 1 ELSE 0 END) as failed_calls
            FROM api_call_logs
            WHERE created_at >= CURRENT_DATE - :days * INTERVAL '1 day'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """)
        
        rows = db.execute(sql, {"days": days}).fetchall()
        daily_usage = [dict(r._mapping) for r in rows]
        
        return {
            "period_days": days,
            "daily_usage": daily_usage,
            "total_calls": sum(r.total_calls for r in rows),
            "total_successful": sum(r.successful_calls for r in rows),
            "total_failed": sum(r.failed_calls for r in rows)
        }
    finally:
        db.close()

@router.get("/usage/by-endpoint")
async def get_usage_by_endpoint(days: int = Query(7, le=90)):
    """Get usage breakdown by endpoint"""
    db = SessionLocal()
    try:
        sql = text("""
            SELECT 
                endpoint,
                COUNT(*) as call_count,
                AVG(response_time_ms) as avg_response_time,
                MAX(response_time_ms) as max_response_time,
                MIN(response_time_ms) as min_response_time,
                SUM(CASE WHEN response_status >= 200 AND response_status < 300 THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN response_status >= 400 THEN 1 ELSE 0 END) as error_count
            FROM api_call_logs
            WHERE created_at >= CURRENT_DATE - :days * INTERVAL '1 day'
            GROUP BY endpoint
            ORDER BY call_count DESC
        """)
        
        rows = db.execute(sql, {"days": days}).fetchall()
        
        return {
            "period_days": days,
            "endpoints": [dict(r._mapping) for r in rows]
        }
    finally:
        db.close()

@router.get("/usage/by-api-key")
async def get_usage_by_api_key(days: int = Query(30, le=90)):
    """Get usage breakdown by API key (for billing)"""
    db = SessionLocal()
    try:
        sql = text("""
            SELECT 
                api_key,
                COUNT(*) as total_calls,
                COUNT(DISTINCT DATE(created_at)) as active_days,
                AVG(response_time_ms) as avg_response_time,
                SUM(CASE WHEN response_status >= 200 AND response_status < 300 THEN 1 ELSE 0 END) as successful_calls,
                SUM(CASE WHEN response_status >= 400 THEN 1 ELSE 0 END) as failed_calls,
                MIN(created_at) as first_call,
                MAX(created_at) as last_call
            FROM api_call_logs
            WHERE created_at >= CURRENT_DATE - :days * INTERVAL '1 day'
            GROUP BY api_key
            ORDER BY total_calls DESC
        """)
        
        rows = db.execute(sql, {"days": days}).fetchall()
        
        return {
            "period_days": days,
            "api_keys": [dict(r._mapping) for r in rows]
        }
    finally:
        db.close()

@router.get("/popular-searches")
async def get_popular_searches(limit: int = Query(20, le=100)):
    """Get most popular search queries"""
    db = SessionLocal()
    try:
        sql = text("""
            SELECT 
                SUBSTRING(query_params FROM 'q=([^&]+)') as query,
                COUNT(*) as search_count,
                AVG(response_time_ms) as avg_response_time
            FROM api_call_logs
            WHERE endpoint LIKE '%/search%'
                AND created_at >= CURRENT_DATE - INTERVAL '30 days'
                AND query_params LIKE '%q=%'
            GROUP BY query
            ORDER BY search_count DESC
            LIMIT :limit
        """)
        
        rows = db.execute(sql, {"limit": limit}).fetchall()
        
        return {
            "top_searches": [dict(r._mapping) for r in rows if r.query]
        }
    finally:
        db.close()

@router.get("/dashboard")
async def get_dashboard_overview():
    """Get comprehensive dashboard overview with insights"""
    db = SessionLocal()
    try:
        # Database content
        content = {
            "icd10_codes": db.execute(text("SELECT COUNT(*) FROM icd10_codes")).scalar(),
            "icd11_codes": db.execute(text("SELECT COUNT(*) FROM icd11_codes")).scalar(),
            "generic_drugs": db.execute(text("SELECT COUNT(*) FROM generic_ingredients")).scalar(),
            "brand_drugs": db.execute(text("SELECT COUNT(*) FROM indian_brand_drugs")).scalar(),
            "abhbp_procedures": db.execute(text("SELECT COUNT(*) FROM abhbp_procedures")).scalar()
        }
        
        # Usage metrics
        usage = {
            "total_calls": db.execute(text("SELECT COUNT(*) FROM api_call_logs")).scalar(),
            "calls_today": db.execute(text(
                "SELECT COUNT(*) FROM api_call_logs WHERE DATE(created_at) = CURRENT_DATE"
            )).scalar(),
            "calls_yesterday": db.execute(text(
                "SELECT COUNT(*) FROM api_call_logs WHERE DATE(created_at) = CURRENT_DATE - 1"
            )).scalar(),
            "calls_this_week": db.execute(text(
                "SELECT COUNT(*) FROM api_call_logs WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'"
            )).scalar(),
            "calls_this_month": db.execute(text(
                "SELECT COUNT(*) FROM api_call_logs WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)"
            )).scalar()
        }
        
        # Active users
        users = {
            "total_api_keys": db.execute(text("SELECT COUNT(DISTINCT api_key) FROM api_call_logs")).scalar(),
            "active_today": db.execute(text(
                "SELECT COUNT(DISTINCT api_key) FROM api_call_logs WHERE DATE(created_at) = CURRENT_DATE"
            )).scalar(),
            "active_this_week": db.execute(text(
                "SELECT COUNT(DISTINCT api_key) FROM api_call_logs WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'"
            )).scalar(),
            "active_this_month": db.execute(text(
                "SELECT COUNT(DISTINCT api_key) FROM api_call_logs WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)"
            )).scalar()
        }
        
        # Performance
        perf = db.execute(text("""
            SELECT 
                AVG(response_time_ms) as avg_response_time,
                MAX(response_time_ms) as max_response_time,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_response_time
            FROM api_call_logs
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
        """)).fetchone()
        
        performance = {
            "avg_response_time_ms": round(perf.avg_response_time, 2) if perf.avg_response_time else 0,
            "max_response_time_ms": round(perf.max_response_time, 2) if perf.max_response_time else 0,
            "p95_response_time_ms": round(perf.p95_response_time, 2) if perf.p95_response_time else 0
        }
        
        # Success rate
        success = db.execute(text("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN response_status >= 200 AND response_status < 300 THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN response_status >= 400 THEN 1 ELSE 0 END) as errors
            FROM api_call_logs
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
        """)).fetchone()
        
        health = {
            "success_rate": round((success.successful / success.total * 100), 2) if success.total > 0 else 0,
            "error_rate": round((success.errors / success.total * 100), 2) if success.total > 0 else 0,
            "total_errors": success.errors
        }
        
        # Top endpoints
        top_endpoints = db.execute(text("""
            SELECT endpoint, COUNT(*) as calls
            FROM api_call_logs
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY endpoint
            ORDER BY calls DESC
            LIMIT 5
        """)).fetchall()
        
        # Growth (compare to previous period)
        prev_week = db.execute(text(
            "SELECT COUNT(*) FROM api_call_logs WHERE created_at >= CURRENT_DATE - INTERVAL '14 days' AND created_at < CURRENT_DATE - INTERVAL '7 days'"
        )).scalar()
        
        growth = {
            "calls_growth_percent": round(((usage["calls_this_week"] - prev_week) / prev_week * 100), 2) if prev_week > 0 else 0,
            "calls_growth_absolute": usage["calls_this_week"] - prev_week
        }
        
        return {
            "content": content,
            "usage": usage,
            "users": users,
            "performance": performance,
            "health": health,
            "growth": growth,
            "top_endpoints": [{"endpoint": e.endpoint, "calls": e.calls} for e in top_endpoints],
            "timestamp": db.execute(text("SELECT NOW()")).scalar().isoformat()
        }
    finally:
        db.close()

@router.get("/performance")
async def get_performance_metrics(days: int = Query(7, le=90)):
    """Get API performance metrics"""
    db = SessionLocal()
    try:
        sql = text("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as total_calls,
                AVG(response_time_ms) as avg_response_time,
                MIN(response_time_ms) as min_response_time,
                MAX(response_time_ms) as max_response_time,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_response_time,
                PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY response_time_ms) as p99_response_time
            FROM api_call_logs
            WHERE created_at >= CURRENT_DATE - :days * INTERVAL '1 day'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """)
        
        rows = db.execute(sql, {"days": days}).fetchall()
        
        return {
            "period_days": days,
            "performance": [dict(r._mapping) for r in rows]
        }
    finally:
        db.close()

@router.get("/errors")
async def get_error_analysis(days: int = Query(7, le=90)):
    """Get error analysis"""
    db = SessionLocal()
    try:
        sql = text("""
            SELECT 
                response_status,
                endpoint,
                COUNT(*) as error_count,
                MAX(created_at) as last_occurrence
            FROM api_call_logs
            WHERE response_status >= 400
                AND created_at >= CURRENT_DATE - :days * INTERVAL '1 day'
            GROUP BY response_status, endpoint
            ORDER BY error_count DESC
        """)
        
        rows = db.execute(sql, {"days": days}).fetchall()
        
        return {
            "period_days": days,
            "errors": [dict(r._mapping) for r in rows]
        }
    finally:
        db.close()
