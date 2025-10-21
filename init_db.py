#!/usr/bin/env python3

import asyncio
import pandas as pd
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from app.db.models import ICD10
from app.core.config import settings

async def init_database():
    """Initialize database with comprehensive medical terminology data"""
    
    # Create engine
    engine = create_engine(settings.database_url)
    
    # Create all tables
    print("🏗️  Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Enable PostgreSQL extensions for better search
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent;"))
            conn.commit()
            print("✅ PostgreSQL extensions enabled")
        except Exception as e:
            print(f"⚠️  Extension setup: {e}")
    
    print("✅ Database tables created")
    
    # Download real data if not exists
    if not os.path.exists('data/icd10_full.csv'):
        print("📥 Downloading real medical terminology data...")
        os.system('python3 data/download_real_data.py')
    
    # Load ICD-10 data
    await load_icd10_data(engine)
    

    
    # Create search indexes
    await create_search_indexes(engine)
    
    print("🎉 Enterprise database initialization complete!")

async def load_icd10_data(engine):
    """Load comprehensive ICD-10 data"""
    try:
        print("📊 Loading ICD-10 data...")
        df = pd.read_csv('data/icd10_full.csv')
        
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Clear existing data
        session.query(ICD10).delete()
        session.commit()
        
        count = 0
        batch_size = 1000
        
        for _, row in df.iterrows():
            icd10 = ICD10(
                code=row['code'],
                term=row['term'],
                chapter=row.get('chapter', ''),
                parent_code=row.get('parent_code') if pd.notna(row.get('parent_code')) else None,
                active=True
            )
            session.add(icd10)
            count += 1
            
            if count % batch_size == 0:
                session.commit()
                print(f"  📈 Loaded {count} ICD-10 codes...")
        
        session.commit()
        session.close()
        print(f"✅ Loaded {count} ICD-10 codes successfully")
        
    except FileNotFoundError:
        print("❌ ICD-10 data file not found")
        raise
    except Exception as e:
        print(f"❌ Error loading ICD-10 data: {e}")
        raise



async def create_search_indexes(engine):
    """Create optimized search indexes for enterprise performance"""
    print("🚀 Creating search indexes...")
    
    indexes = [
        # ICD-10 search indexes
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_icd10_code_gin ON icd10 USING gin(code gin_trgm_ops);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_icd10_term_gin ON icd10 USING gin(term gin_trgm_ops);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_icd10_chapter ON icd10(chapter);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_icd10_active ON icd10(active) WHERE active = true;",
        

        
        # Composite indexes for complex queries
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_icd10_active_term ON icd10(active, term) WHERE active = true;",
    ]
    
    with engine.connect() as conn:
        for idx_sql in indexes:
            try:
                conn.execute(text(idx_sql))
                conn.commit()
            except Exception as e:
                print(f"⚠️  Index creation: {e}")
    
    print("✅ Search indexes created")

if __name__ == "__main__":
    asyncio.run(init_database())