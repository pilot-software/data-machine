"""
SNOMED CT Database Models
SQLAlchemy ORM models for SNOMED Indian Drug Database
"""

from sqlalchemy import Column, BigInteger, String, Text, Date, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class SnomedSubstance(Base):
    __tablename__ = "snomed_substances"
    
    snomed_id = Column(BigInteger, primary_key=True)
    substance_name = Column(Text, nullable=False)
    cas_number = Column(String(50))
    unii = Column(String(20))
    substance_description = Column(Text)
    molecular_weight = Column(String(50))
    toxicity = Column(Text)
    smile = Column(Text)
    inchi = Column(Text)
    iupac_name = Column(Text)
    molecular_formula = Column(String(200))
    last_updated = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)


class SnomedGeneric(Base):
    __tablename__ = "snomed_generics"
    
    snomed_id = Column(BigInteger, primary_key=True)
    generic_name = Column(Text, nullable=False)
    substance_ids = Column(Text)
    route_of_admin = Column(Text)
    dose_form = Column(Text)
    therapeutic_role = Column(Text)
    indication = Column(Text)
    contra_indication = Column(Text)
    drug_interactions = Column(Text)
    drug_classification = Column(Text)
    source_regulatory = Column(Text)
    last_updated = Column(Date)
    search_vector = Column(TSVECTOR)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    brands = relationship("SnomedBrand", back_populates="generic")


class SnomedBrand(Base):
    __tablename__ = "snomed_brands"
    
    snomed_id = Column(BigInteger, primary_key=True)
    brand_name = Column(Text, nullable=False)
    product_id = Column(BigInteger, ForeignKey('snomed_products.snomed_id'))
    supplier_id = Column(BigInteger, ForeignKey('snomed_suppliers.snomed_id'))
    generic_id = Column(BigInteger, ForeignKey('snomed_generics.snomed_id'))
    license_number = Column(String(100))
    license_status = Column(String(20))
    excipient = Column(Text)
    last_updated = Column(Date)
    search_vector = Column(TSVECTOR)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    generic = relationship("SnomedGeneric", back_populates="brands")
    product = relationship("SnomedProduct", back_populates="brands")
    supplier = relationship("SnomedSupplier", back_populates="brands")


class SnomedProduct(Base):
    __tablename__ = "snomed_products"
    
    snomed_id = Column(BigInteger, primary_key=True)
    product_name = Column(Text, nullable=False)
    search_vector = Column(TSVECTOR)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    brands = relationship("SnomedBrand", back_populates="product")


class SnomedSupplier(Base):
    __tablename__ = "snomed_suppliers"
    
    snomed_id = Column(BigInteger, primary_key=True)
    supplier_name = Column(Text, nullable=False)
    country = Column(String(100))
    search_vector = Column(TSVECTOR)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    brands = relationship("SnomedBrand", back_populates="supplier")
