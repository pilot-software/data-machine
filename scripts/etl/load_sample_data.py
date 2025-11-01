"""
Load sample Indian drug data into database
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://samirkolhe@localhost:5432/hms_terminology')

# RxNorm mapping for common generics
RXNORM_MAPPING = {
    'Acetaminophen': ('202433', 'N02BE01'),
    'Metformin': ('6809', 'A10BA02'),
    'Amlodipine': ('17767', 'C08CA01'),
    'Atorvastatin': ('83367', 'C10AA05'),
    'Omeprazole': ('7646', 'A02BC01'),
    'Azithromycin': ('18631', 'J01FA10'),
    'Amoxicillin': ('723', 'J01CA04'),
    'Ibuprofen': ('5640', 'M01AE01'),
    'Aspirin': ('1191', 'N02BA01'),
    'Pantoprazole': ('40790', 'A02BC02'),
    'Telmisartan': ('73494', 'C09CA07'),
    'Losartan': ('52175', 'C09CA01'),
    'Levothyroxine': ('10582', 'H03AA01'),
    'Cetirizine': ('20610', 'R06AE07'),
    'Montelukast': ('88249', 'R03DC03'),
    'Levocetirizine': ('349199', 'R06AE09'),
    'Ranitidine': ('9143', 'A02BA02'),
    'Domperidone': ('3638', 'A03FA03'),
    'Norfloxacin': ('7517', 'J01MA06'),
    'Tinidazole': ('10627', 'P01AB02'),
    'Ciprofloxacin': ('2551', 'J01MA02'),
    'Clavulanic Acid': ('20481', 'J01CR02'),
    'Glimepiride': ('25789', 'A10BB12'),
}

def load_data():
    print("🚀 Loading sample Indian drug data...")
    
    # Read CSV
    df = pd.read_csv('data/sample_indian_drugs.csv')
    print(f"📊 Found {len(df)} drugs")
    
    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # 1. Load generic ingredients
    print("📦 Loading generic ingredients...")
    generics = df[['generic_name']].drop_duplicates()
    
    ingredient_map = {}
    for _, row in generics.iterrows():
        generic = row['generic_name']
        
        # Handle combination drugs
        if '+' in generic:
            ingredients = [g.strip() for g in generic.split('+')]
            generic = ingredients[0]  # Use first ingredient for now
        
        rxnorm_cui, atc_code = RXNORM_MAPPING.get(generic, (None, None))
        
        cursor.execute("""
            INSERT INTO generic_ingredients 
            (ingredient_name, rxnorm_cui, atc_code, therapeutic_class)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (rxnorm_cui) DO UPDATE 
            SET ingredient_name = EXCLUDED.ingredient_name
            RETURNING ingredient_id, rxnorm_cui
        """, (generic, rxnorm_cui, atc_code, 'Common Medicine'))
        
        result = cursor.fetchone()
        if result:
            ingredient_map[generic] = result[0]
    
    conn.commit()
    print(f"✅ Loaded {len(ingredient_map)} generic ingredients")
    
    # 2. Load brand drugs
    print("💊 Loading brand drugs...")
    brand_data = []
    
    for _, row in df.iterrows():
        generic = row['generic_name']
        
        # Handle combination drugs
        if '+' in generic:
            ingredients = [g.strip() for g in generic.split('+')]
            generic = ingredients[0]
        
        ingredient_id = ingredient_map.get(generic)
        if not ingredient_id:
            continue
        
        rxnorm_cui, _ = RXNORM_MAPPING.get(generic, (None, None))
        
        brand_data.append((
            row['drug_name'],
            row['manufacturer'],
            ingredient_id,
            rxnorm_cui,
            row['strength'],
            row['dosage_form'],
            'Oral',  # route
            row.get('schedule', ''),
            '',  # cdsco_approval
            float(row['mrp']),
            row['pack_size'],
            row['prescription_required'] == 'TRUE',
            row['prescription_required'] == 'FALSE',
        ))
    
    execute_batch(cursor, """
        INSERT INTO indian_brand_drugs 
        (brand_name, manufacturer, ingredient_id, rxnorm_cui, 
         strength, dosage_form, route, schedule, cdsco_approval,
         mrp, pack_size, prescription_required, otc_available)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (brand_name, strength, dosage_form) DO UPDATE
        SET mrp = EXCLUDED.mrp,
            manufacturer = EXCLUDED.manufacturer,
            updated_at = NOW()
    """, brand_data, page_size=100)
    
    conn.commit()
    print(f"✅ Loaded {len(brand_data)} brand drugs")
    
    # 3. Statistics
    cursor.execute("SELECT COUNT(*) FROM generic_ingredients")
    generic_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM indian_brand_drugs")
    brand_count = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    print("\n📊 Database Statistics:")
    print(f"   Generic Ingredients: {generic_count}")
    print(f"   Brand Drugs: {brand_count}")
    print("\n✅ Sample data loaded successfully!")
    print("\n🎯 Test the API:")
    print("   curl 'http://localhost:8001/api/v1/drugs/search?query=crocin'")
    print("   curl 'http://localhost:8001/api/v1/drugs/generic/Acetaminophen'")

if __name__ == "__main__":
    load_data()
