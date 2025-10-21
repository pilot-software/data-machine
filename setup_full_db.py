#!/usr/bin/env python3
"""
Setup complete database with full ICD-10 and ICD-11 datasets
"""

import asyncpg
import asyncio
import json
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def setup_database():
    """Setup database with proper schema and full datasets"""
    
    # Database connection from environment
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is required")
    
    # Extract database name and create connection URL for postgres db
    db_name = db_url.split('/')[-1]
    postgres_url = db_url.rsplit('/', 1)[0] + '/postgres'
    
    try:
        # Connect to default postgres database first
        conn = await asyncpg.connect(postgres_url)
        
        # Create database if not exists
        try:
            await conn.execute(f"CREATE DATABASE {db_name}")
            print(f"✅ Database '{db_name}' created")
        except:
            print(f"📊 Database '{db_name}' already exists")
        
        await conn.close()
        
        # Connect to our database
        conn = await asyncpg.connect(db_url)
        
        # Create tables with proper schema
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS icd10_codes (
                id SERIAL PRIMARY KEY,
                code VARCHAR(20) UNIQUE NOT NULL,
                term TEXT NOT NULL,
                short_desc TEXT,
                chapter TEXT,
                category VARCHAR(10),
                search_vector tsvector,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS icd11_codes (
                id SERIAL PRIMARY KEY,
                code VARCHAR(20) UNIQUE NOT NULL,
                title TEXT NOT NULL,
                definition TEXT,
                chapter TEXT,
                url TEXT,
                search_vector tsvector,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_icd10_search ON icd10_codes USING GIN(search_vector)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_icd10_code ON icd10_codes(code)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_icd11_search ON icd11_codes USING GIN(search_vector)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_icd11_code ON icd11_codes(code)")
        
        print("✅ Database schema created")
        
        # Load ICD-10 data (71,704 codes)
        if os.path.exists('data/icd10_full_processed.csv'):
            print("🔄 Loading ICD-10 data (71,704 codes)...")
            df_icd10 = pd.read_csv('data/icd10_full_processed.csv')
            
            batch_size = 1000
            for i in range(0, len(df_icd10), batch_size):
                batch = df_icd10.iloc[i:i+batch_size]
                
                for _, row in batch.iterrows():
                    search_text = f"{row['term']} {row.get('short_desc', '')}"
                    await conn.execute("""
                        INSERT INTO icd10_codes (code, term, short_desc, chapter, category, search_vector)
                        VALUES ($1, $2, $3, $4, $5, to_tsvector('english', $6))
                        ON CONFLICT (code) DO UPDATE SET
                            term = EXCLUDED.term,
                            short_desc = EXCLUDED.short_desc,
                            chapter = EXCLUDED.chapter,
                            search_vector = EXCLUDED.search_vector
                    """, row['code'], row['term'], row.get('short_desc'), 
                         row.get('chapter'), row.get('category'), search_text)
                
                print(f"  📈 Loaded {min(i+batch_size, len(df_icd10))}/{len(df_icd10)} ICD-10 codes")
        
        # Load ICD-11 data (4,239 codes)
        if os.path.exists('data/icd11_who_api.json'):
            print("🔄 Loading ICD-11 data (4,239 codes)...")
            with open('data/icd11_who_api.json', 'r') as f:
                icd11_data = json.load(f)
            
            for code_data in icd11_data:
                search_text = f"{code_data['title']} {code_data.get('definition', '')}"
                await conn.execute("""
                    INSERT INTO icd11_codes (code, title, definition, chapter, url, search_vector)
                    VALUES ($1, $2, $3, $4, $5, to_tsvector('english', $6))
                    ON CONFLICT (code) DO UPDATE SET
                        title = EXCLUDED.title,
                        definition = EXCLUDED.definition,
                        chapter = EXCLUDED.chapter,
                        url = EXCLUDED.url,
                        search_vector = EXCLUDED.search_vector
                """, code_data['code'], code_data['title'], code_data.get('definition'),
                     code_data.get('chapter'), code_data.get('url'), search_text)
        
        # Get final counts
        icd10_count = await conn.fetchval("SELECT COUNT(*) FROM icd10_codes")
        icd11_count = await conn.fetchval("SELECT COUNT(*) FROM icd11_codes")
        
        print(f"\n🎉 Database setup complete!")
        print(f"📊 Final counts:")
        print(f"  ICD-10: {icd10_count:,} codes")
        print(f"  ICD-11: {icd11_count:,} codes")
        print(f"  Total: {icd10_count + icd11_count:,} medical codes")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Database setup error: {e}")

if __name__ == "__main__":
    asyncio.run(setup_database())