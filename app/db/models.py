from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import TSVECTOR
from datetime import datetime
from app.db.database import Base


class ICD10(Base):
    __tablename__ = "icd10_codes"
    
    id = Column(Integer, primary_key=True)
    code = Column(String(20), nullable=False, unique=True)
    term = Column(Text, nullable=False)
    short_desc = Column(Text)
    chapter = Column(Text)
    category = Column(String(10))
    parent_code = Column(String(20))
    active = Column(Boolean, default=True)
    billable = Column(Boolean, default=True)
    search_vector = Column(TSVECTOR)
    created_at = Column(DateTime, default=datetime.utcnow)



