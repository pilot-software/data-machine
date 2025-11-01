from sqlalchemy import Column, String, Boolean, DateTime, Text, Index, Integer
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
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


class LOINC(Base):
    __tablename__ = "loinc"
    
    code = Column(String(20), primary_key=True)
    component = Column(Text, nullable=False)
    property = Column(String(100))
    system = Column(String(100))
    method = Column(String(100))
    unit = Column(String(50))
    active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_loinc_component_gin', 'component', postgresql_using='gin', postgresql_ops={'component': 'gin_trgm_ops'}),
        Index('idx_loinc_active', 'active'),
    )


class SymptomMaster(Base):
    __tablename__ = "symptoms_master"
    
    id = Column(String(50), primary_key=True)
    canonical_term = Column(Text, nullable=False)
    synonyms = Column(JSONB, default=[])
    tags = Column(JSONB, default=[])
    icd10_codes = Column(JSONB, default=[])
    active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_symptom_term_gin', 'canonical_term', postgresql_using='gin', postgresql_ops={'canonical_term': 'gin_trgm_ops'}),
        Index('idx_symptom_active', 'active'),
    )



