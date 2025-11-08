#!/usr/bin/env python3
"""Load AB-HBP data into PostgreSQL"""

import pandas as pd
import psycopg2
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).parent.parent.parent / "data"
CSV_PATH = DATA_DIR / "abhbp_packages.csv"

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "hms_terminology"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres")
    )

def load_abhbp():
    if not CSV_PATH.exists():
        print("❌ CSV not found. Run download_abhbp_data.py first")
        return
    
    print("📊 Loading AB-HBP data...")
    df = pd.read_csv(CSV_PATH)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    inserted = 0
    for _, row in df.iterrows():
        package_code = str(row.get('package_code', '')).strip()
        package_name = str(row.get('package_name', '')).strip()
        
        if not package_code or package_code == 'nan':
            continue
        
        try:
            cur.execute("""
                INSERT INTO abhbp_procedures 
                (package_code, package_name, specialty, procedure_type, base_rate, active)
                VALUES (%s, %s, %s, %s, %s, TRUE)
                ON CONFLICT (package_code) DO UPDATE SET
                    package_name = EXCLUDED.package_name,
                    base_rate = EXCLUDED.base_rate,
                    updated_at = NOW()
            """, (
                package_code,
                package_name,
                row.get('specialty'),
                row.get('procedure_name'),
                row.get('base_rate') if pd.notna(row.get('base_rate')) else None
            ))
            conn.commit()
            inserted += 1
        except Exception as e:
            conn.rollback()
            print(f"⚠️  Error: {e}")
            break
    
    cur.close()
    conn.close()
    
    print(f"✅ Loaded {inserted} AB-HBP packages")

if __name__ == "__main__":
    load_abhbp()
