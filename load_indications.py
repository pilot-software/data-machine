"""
Load drug indications (symptoms/conditions) into database
"""

import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://samirkolhe@localhost:5432/hms_terminology')

def load_indications():
    print("🔄 Loading drug indications...")
    
    # Read indications CSV
    df = pd.read_csv('data/drug_indications.csv')
    print(f"📊 Found {len(df)} generic drugs with indications")
    
    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Update generic ingredients with indications
    updated = 0
    for _, row in df.iterrows():
        cursor.execute("""
            UPDATE generic_ingredients 
            SET 
                indications = %s,
                symptoms = %s,
                conditions = %s,
                updated_at = NOW()
            WHERE ingredient_name = %s
        """, (
            row['indications'],
            row['symptoms'],
            row['conditions'],
            row['generic_name']
        ))
        
        if cursor.rowcount > 0:
            updated += 1
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"✅ Updated {updated} generic ingredients with indications")
    print("\n🎯 Test symptom search:")
    print("   curl 'http://localhost:8001/api/v1/drugs/search?query=fever'")
    print("   curl 'http://localhost:8001/api/v1/drugs/search?query=headache'")
    print("   curl 'http://localhost:8001/api/v1/drugs/search/by-symptom?symptom=diabetes'")

if __name__ == "__main__":
    load_indications()
