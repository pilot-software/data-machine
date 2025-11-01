"""
Load real drug data into database
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://samirkolhe@localhost:5432/hms_terminology')

print("🚀 Loading real drug data into database...\n")

# Connect to database
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# ============================================
# 1. Load RxNorm generics
# ============================================
print("📦 Step 1: Loading generic ingredients...")

df_rxnorm = pd.read_csv('data/real/rxnorm_generics.csv')
df_indications = pd.read_csv('data/real/drug_indications.csv')

# Merge indications
df_generics = df_rxnorm.merge(df_indications, left_on='generic_name', right_on='generic', how='left')

ingredient_map = {}
for _, row in df_generics.iterrows():
    cursor.execute("""
        INSERT INTO generic_ingredients 
        (ingredient_name, rxnorm_cui, atc_code, indications, symptoms, therapeutic_class)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (rxnorm_cui) DO UPDATE 
        SET ingredient_name = EXCLUDED.ingredient_name,
            indications = EXCLUDED.indications,
            symptoms = EXCLUDED.symptoms
        RETURNING ingredient_id, rxnorm_cui
    """, (
        row['generic_name'],
        row['rxnorm_cui'],
        row.get('atc_code'),
        row.get('indications'),
        row.get('symptoms'),
        'Common Medicine'
    ))
    
    result = cursor.fetchone()
    if result:
        ingredient_map[row['generic_name']] = result[0]

conn.commit()
print(f"✅ Loaded {len(ingredient_map)} generic ingredients\n")

# ============================================
# 2. Load Indian brands
# ============================================
print("📦 Step 2: Loading Indian brand drugs...")

df_brands = pd.read_csv('data/real/indian_brands.csv')

brand_data = []
for _, row in df_brands.iterrows():
    ingredient_id = ingredient_map.get(row['generic'])
    if not ingredient_id:
        continue
    
    # Get RxNorm CUI
    cursor.execute("""
        SELECT rxnorm_cui FROM generic_ingredients WHERE ingredient_id = %s
    """, (ingredient_id,))
    rxnorm_result = cursor.fetchone()
    rxnorm_cui = rxnorm_result[0] if rxnorm_result else None
    
    brand_data.append((
        row['brand'],
        row['manufacturer'],
        ingredient_id,
        rxnorm_cui,
        row['strength'],
        row['form'],
        'Oral',
        '',
        '',
        float(row['mrp']),
        '10 tablets',
        False,
        True
    ))

execute_batch(cursor, """
    INSERT INTO indian_brand_drugs 
    (brand_name, manufacturer, ingredient_id, rxnorm_cui, 
     strength, dosage_form, route, schedule, cdsco_approval,
     mrp, pack_size, prescription_required, otc_available)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (brand_name, strength, dosage_form) DO UPDATE
    SET mrp = EXCLUDED.mrp,
        manufacturer = EXCLUDED.manufacturer
""", brand_data, page_size=100)

conn.commit()
print(f"✅ Loaded {len(brand_data)} brand drugs\n")

# ============================================
# 3. Statistics
# ============================================
cursor.execute("SELECT COUNT(*) FROM generic_ingredients")
generic_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM indian_brand_drugs")
brand_count = cursor.fetchone()[0]

cursor.close()
conn.close()

print("=" * 60)
print("📊 DATABASE STATISTICS")
print("=" * 60)
print(f"✅ Generic Ingredients: {generic_count}")
print(f"✅ Brand Drugs: {brand_count}")
print("\n🎯 Test the API:")
print("  curl 'http://localhost:8001/api/v1/drugs/search?q=crocin'")
print("  curl 'http://localhost:8001/api/v1/drugs/search?q=metformin'")
print("  curl 'http://localhost:8001/api/v1/drugs/search?q=fever'")
print("\n✅ Real data loaded successfully!")
