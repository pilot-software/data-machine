from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.db.models import ICD10
from app.db.database import SessionLocal

class ICD10Repository:
    """Data access layer for ICD-10 codes"""
    
    def __init__(self):
        self.db: Optional[Session] = None
    
    def __enter__(self):
        self.db = SessionLocal()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            self.db.close()
    
    def find_by_code(self, code: str) -> Optional[ICD10]:
        """Find ICD-10 code by exact match"""
        return self.db.query(ICD10).filter(ICD10.code == code).first()
    
    def find_by_code_prefix(self, prefix: str, limit: int = 10) -> List[ICD10]:
        """Find codes starting with prefix"""
        return self.db.query(ICD10).filter(
            ICD10.code.ilike(f"{prefix}%"),
            ICD10.active == True
        ).limit(limit).all()
    
    def find_by_term_prefix(self, term: str, limit: int = 10) -> List[ICD10]:
        """Find codes by term prefix"""
        return self.db.query(ICD10).filter(
            func.lower(ICD10.term).like(f"{term.lower()}%"),
            ICD10.active == True
        ).limit(limit).all()
    
    def find_by_similarity(self, query: str, threshold: float = 0.3, limit: int = 20) -> List[ICD10]:
        """Find codes using similarity matching"""
        return self.db.query(ICD10).filter(
            or_(
                func.similarity(ICD10.term, query) > threshold,
                func.similarity(ICD10.code, query) > threshold
            ),
            ICD10.active == True
        ).order_by(
            (func.similarity(ICD10.term, query) + func.similarity(ICD10.code, query)).desc()
        ).limit(limit).all()
    
    def find_children(self, parent_code: str, limit: int = 20) -> List[ICD10]:
        """Find child codes"""
        return self.db.query(ICD10).filter(
            ICD10.parent_code == parent_code,
            ICD10.active == True
        ).limit(limit).all()
    
    def find_siblings(self, parent_code: str, exclude_code: str, limit: int = 10) -> List[ICD10]:
        """Find sibling codes"""
        return self.db.query(ICD10).filter(
            ICD10.parent_code == parent_code,
            ICD10.code != exclude_code,
            ICD10.active == True
        ).limit(limit).all()
    
    def count_total(self) -> int:
        """Get total count of active codes"""
        return self.db.query(ICD10).filter(ICD10.active == True).count()
    
    def find_with_chapter_filter(self, query: str, chapter_filter: str, limit: int = 10) -> List[ICD10]:
        """Find codes with chapter filtering"""
        return self.db.query(ICD10).filter(
            ICD10.term.ilike(f"%{query}%"),
            ICD10.chapter.ilike(f"%{chapter_filter}%"),
            ICD10.active == True
        ).limit(limit).all()
    
    def find_by_multiple_criteria(self, query: str, chapter_filter: Optional[str] = None, 
                                 include_inactive: bool = False, limit: int = 10) -> List[ICD10]:
        """Find codes by multiple search criteria"""
        base_query = self.db.query(ICD10)
        
        if not include_inactive:
            base_query = base_query.filter(ICD10.active == True)
        
        if chapter_filter:
            base_query = base_query.filter(ICD10.chapter.ilike(f"%{chapter_filter}%"))
        
        return base_query.filter(
            or_(
                ICD10.code.ilike(f"%{query}%"),
                ICD10.term.ilike(f"%{query}%")
            )
        ).limit(limit).all()
    
    def get_similarity_score(self, code: str, query: str) -> float:
        """Get similarity score for a specific code"""
        result = self.db.execute(
            func.similarity(ICD10.term, query)
        ).where(ICD10.code == code).scalar()
        return result or 0.0