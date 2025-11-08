from sqlalchemy import text
from app.db.database import SessionLocal
import time
import logging

logger = logging.getLogger(__name__)

class SearchLogger:
    """Log search queries to database"""
    
    @staticmethod
    def log_search(query: str, results_count: int, response_time_ms: float, cache_hit: bool = False, user_id: str = None):
        """Log search query asynchronously"""
        try:
            db = SessionLocal()
            db.execute(text("""
                INSERT INTO search_logs_master (user_id, query, results_count, response_time_ms, cache_hit)
                VALUES (:user_id, :query, :results_count, :response_time_ms, :cache_hit)
            """), {
                "user_id": user_id,
                "query": query[:500],  # Limit query length
                "results_count": results_count,
                "response_time_ms": response_time_ms,
                "cache_hit": cache_hit
            })
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Search logging failed: {e}")

search_logger = SearchLogger()
