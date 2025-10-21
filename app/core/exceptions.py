from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Database connection or query error"""
    pass

class ValidationError(Exception):
    """Input validation error"""
    pass

class ServiceUnavailableError(Exception):
    """External service unavailable"""
    pass

def handle_database_error(e: Exception, operation: str = "database operation"):
    """Handle database errors securely"""
    logger.error(f"Database error during {operation}: {str(e)}")
    raise HTTPException(
        status_code=503,
        detail="Database service temporarily unavailable"
    )

def handle_validation_error(e: Exception):
    """Handle validation errors"""
    logger.warning(f"Validation error: {str(e)}")
    raise HTTPException(
        status_code=400,
        detail="Invalid input parameters"
    )

def handle_service_error(e: Exception, service: str = "service"):
    """Handle service errors"""
    logger.error(f"{service} error: {str(e)}")
    raise HTTPException(
        status_code=503,
        detail=f"{service} temporarily unavailable"
    )