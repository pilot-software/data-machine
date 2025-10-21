import logging
import logging.config
import json
import sys
from datetime import datetime
from typing import Dict, Any

class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'operation'):
            log_entry['operation'] = record.operation
        if hasattr(record, 'duration_ms'):
            log_entry['duration_ms'] = record.duration_ms
        
        return json.dumps(log_entry)

def setup_logging(log_level: str = "INFO") -> None:
    """Setup structured logging configuration"""
    
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'structured': {
                '()': StructuredFormatter,
            },
            'simple': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'structured',
                'stream': sys.stdout
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': log_level,
                'formatter': 'structured',
                'filename': 'logs/app.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'structured',
                'filename': 'logs/error.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            }
        },
        'loggers': {
            'app': {
                'level': log_level,
                'handlers': ['console', 'file', 'error_file'],
                'propagate': False
            },
            'sqlalchemy.engine': {
                'level': 'WARNING',
                'handlers': ['file'],
                'propagate': False
            },
            'uvicorn': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            }
        },
        'root': {
            'level': log_level,
            'handlers': ['console', 'file']
        }
    }
    
    logging.config.dictConfig(logging_config)

class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter for adding context to logs"""
    
    def __init__(self, logger: logging.Logger, extra: Dict[str, Any]):
        super().__init__(logger, extra)
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Add extra context to log records"""
        kwargs['extra'] = {**self.extra, **kwargs.get('extra', {})}
        return msg, kwargs

def get_logger(name: str, **context) -> LoggerAdapter:
    """Get logger with context"""
    logger = logging.getLogger(name)
    return LoggerAdapter(logger, context)

# Performance logging helpers
def log_performance(logger: logging.Logger, operation: str, duration_ms: float, **extra):
    """Log performance metrics"""
    logger.info(
        f"Performance: {operation} completed in {duration_ms:.2f}ms",
        extra={'operation': operation, 'duration_ms': duration_ms, **extra}
    )

def log_database_operation(logger: logging.Logger, operation: str, table: str, 
                          duration_ms: float, rows_affected: int = None):
    """Log database operations"""
    extra = {
        'operation': operation,
        'table': table,
        'duration_ms': duration_ms
    }
    if rows_affected is not None:
        extra['rows_affected'] = rows_affected
    
    logger.info(f"Database: {operation} on {table} - {duration_ms:.2f}ms", extra=extra)

def log_cache_operation(logger: logging.Logger, operation: str, key: str, hit: bool = None):
    """Log cache operations"""
    extra = {'operation': operation, 'cache_key': key}
    if hit is not None:
        extra['cache_hit'] = hit
    
    logger.info(f"Cache: {operation} - {key}", extra=extra)