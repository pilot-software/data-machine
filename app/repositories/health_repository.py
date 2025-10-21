from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import SessionLocal
import time

class HealthRepository:
    """Repository for health check database operations"""
    
    def __init__(self):
        self.db: Session = None
    
    def __enter__(self):
        self.db = SessionLocal()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            self.db.close()
    
    def check_database_connection(self) -> Dict[str, Any]:
        """Test basic database connectivity"""
        start_time = time.time()
        try:
            result = self.db.execute(text("SELECT 1")).scalar()
            response_time = round((time.time() - start_time) * 1000, 2)
            
            return {
                'status': 'healthy' if result == 1 else 'unhealthy',
                'response_time_ms': response_time,
                'connection_successful': True
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'response_time_ms': round((time.time() - start_time) * 1000, 2),
                'connection_successful': False,
                'error': str(e)
            }
    
    def get_icd10_count(self) -> int:
        """Get total ICD-10 codes count"""
        try:
            return self.db.execute(text("SELECT COUNT(*) FROM icd10_codes")).scalar() or 0
        except Exception:
            return 0
    
    def get_icd11_count(self) -> int:
        """Get total ICD-11 codes count"""
        try:
            return self.db.execute(text("SELECT COUNT(*) FROM icd11_codes")).scalar() or 0
        except Exception:
            return 0
    
    def check_table_exists(self, table_name: str) -> bool:
        """Check if a table exists"""
        try:
            result = self.db.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table_name)"
            ), {"table_name": table_name}).scalar()
            return bool(result)
        except Exception:
            return False
    
    def get_database_size(self) -> str:
        """Get database size"""
        try:
            result = self.db.execute(text(
                "SELECT pg_size_pretty(pg_database_size(current_database()))"
            )).scalar()
            return result or "Unknown"
        except Exception:
            return "Unknown"
    
    def check_indexes_exist(self) -> Dict[str, bool]:
        """Check if required indexes exist"""
        try:
            indexes = {}
            
            # Check ICD-10 indexes
            icd10_code_idx = self.db.execute(text(
                "SELECT EXISTS (SELECT FROM pg_indexes WHERE indexname = 'idx_icd10_code')"
            )).scalar()
            indexes['icd10_code_index'] = bool(icd10_code_idx)
            
            icd10_search_idx = self.db.execute(text(
                "SELECT EXISTS (SELECT FROM pg_indexes WHERE indexname = 'idx_icd10_search')"
            )).scalar()
            indexes['icd10_search_index'] = bool(icd10_search_idx)
            
            # Check ICD-11 indexes
            icd11_code_idx = self.db.execute(text(
                "SELECT EXISTS (SELECT FROM pg_indexes WHERE indexname = 'idx_icd11_code')"
            )).scalar()
            indexes['icd11_code_index'] = bool(icd11_code_idx)
            
            return indexes
        except Exception:
            return {}