from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging
import os
from app.core.settings import settings
from app.core.service_factory import setup_dependencies
from app.core.exceptions import DatabaseError, ServiceUnavailableError
from app.core.logging_config import setup_logging, get_logger
from app.middleware.rate_limiter import advanced_rate_limit_middleware, rate_limiter_cleanup_task
from app.db.partitioning import partition_manager
from app.db.indexing import index_manager
from app.services.redis_cluster import redis_cluster
from app.api.terminology import router as terminology_router
from app.api.icd10 import router as icd10_router
from app.api.enterprise import router as enterprise_router

# Setup structured logging
setup_logging(settings.log_level.upper())
logger = get_logger('app.main')

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="FastAPI service for HMS terminology management with SNOMED, ICD-10, and LOINC integration",
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],  # Restrict origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Add advanced rate limiting middleware
app.middleware("http")(advanced_rate_limit_middleware)

# Global exception handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.warning(f"Validation error on {request.url}: {exc}")
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid input parameters", "errors": exc.errors()}
    )

@app.exception_handler(DatabaseError)
async def database_exception_handler(request: Request, exc: DatabaseError):
    logger.error(f"Database error on {request.url}: {exc}")
    return JSONResponse(
        status_code=503,
        content={"detail": "Database service temporarily unavailable"}
    )

@app.exception_handler(ServiceUnavailableError)
async def service_exception_handler(request: Request, exc: ServiceUnavailableError):
    logger.error(f"Service error on {request.url}: {exc}")
    return JSONResponse(
        status_code=503,
        content={"detail": "Service temporarily unavailable"}
    )

# Include routers
app.include_router(terminology_router)
app.include_router(icd10_router)
app.include_router(enterprise_router)

@app.on_event("startup")
async def startup_event():
    """Application startup event with full initialization"""
    logger.info(f"Starting HMS Terminology Service")
    
    # Setup dependency injection
    await setup_dependencies()
    logger.info("Dependency injection configured")
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    try:
        # Initialize Redis cluster
        await redis_cluster.setup_redis_sentinel()
        logger.info("Redis cluster initialized")
        
        # Setup database partitioning
        await partition_manager.create_icd10_partitions()
        await partition_manager.create_search_log_partitions()
        logger.info("Database partitioning configured")
        
        # Create performance indexes
        await index_manager.create_performance_indexes()
        await index_manager.create_materialized_views()
        await index_manager.setup_query_optimization()
        logger.info("Database indexing optimized")
        
        # Start background tasks
        asyncio.create_task(rate_limiter_cleanup_task())
        logger.info("Background tasks started")
        
    except Exception as e:
        logger.error(f"Startup initialization error: {e}")
        # Continue startup even if some optimizations fail
    
    logger.info("Application startup completed")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event with cleanup"""
    logger.info("Starting application shutdown")
    
    try:
        # Close Redis connections
        if hasattr(redis_cluster, 'current_master') and redis_cluster.current_master:
            await redis_cluster.current_master.close()
        
        # Close database connections
        from app.db.database import async_engine
        await async_engine.dispose()
        
        logger.info("All connections closed successfully")
        
    except Exception as e:
        logger.error(f"Shutdown cleanup error: {e}")
    
    logger.info("Application shutdown completed")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )