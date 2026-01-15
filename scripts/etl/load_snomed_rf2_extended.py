#!/usr/bin/env python3
"""
Load SNOMED CT RF2 Extended Data (Hierarchies, Definitions, Dosages)
Adds drug classification, clinical definitions, and precise dosage info
"""

import csv
import sys
import logging
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_batch

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RF2_DIR = Path("SnomedCT_IndiaDrugExtensionRF2_PRODUCTION_IN1000189_20251219T120000Z/Snapshot")

def get_db_connection():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        database=os.getenv('DB_NAME', 'medical_library'),
        user=os.getenv('DB_USER', 'samirkolhe'),
        password=os.getenv('DB_PASSWORD', '')
    )

def create_extended_tables(conn):
    """Create tables for RF2 extended data"""
    logger.info("Creating extended tables...")
    
    cursor = conn.cursor()
    
    # Drug hierarchies (IS-A relationships)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS snomed_drug_hierarchy (
            id BIGSERIAL PRIMARY KEY,
            drug_id BIGINT NOT NULL,
            parent_id BIGINT NOT NULL,
            relationship_type VARCHAR(50) DEFAULT 'IS-A',
            active BOOLEAN DEFAULT TRUE,
            UNIQUE(drug_id, parent_id)
        );
        CREATE INDEX IF NOT EXISTS idx_hierarchy_drug ON snomed_drug_hierarchy(drug_id);
        CREATE INDEX IF NOT EXISTS idx_hierarchy_parent ON snomed_drug_hierarchy(parent_id);
    """)
    
    # Clinical definitions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS snomed_drug_definitions (
            id BIGSERIAL PRIMARY KEY,
            drug_id BIGINT NOT NULL UNIQUE,
            definition TEXT,
            language_code VARCHAR(5) DEFAULT 'en'
        );
        CREATE INDEX IF NOT EXISTS idx_definitions_drug ON snomed_drug_definitions(drug_id);
    """)
    
    # Precise dosage info
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS snomed_drug_dosages (
            id BIGSERIAL PRIMARY KEY,
            drug_id BIGINT NOT NULL,
            attribute_type VARCHAR(100),
            value_numeric DECIMAL(10,2),
            value_text VARCHAR(100),
            unit_code BIGINT,
            UNIQUE(drug_id, attribute_type)
        );
        CREATE INDEX IF NOT EXISTS idx_dosages_drug ON snomed_drug_dosages(drug_id);
    """)
    
    # Drug classifications (materialized for fast queries)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS snomed_drug_classes (
            drug_id BIGINT PRIMARY KEY,
            drug_name VARCHAR(500),
            is_antibiotic BOOLEAN DEFAULT FALSE,
            is_analgesic BOOLEAN DEFAULT FALSE,
            is_antihypertensive BOOLEAN DEFAULT FALSE,
            is_antidiabetic BOOLEAN DEFAULT FALSE,
            is_antiinflammatory BOOLEAN DEFAULT FALSE,
            drug_class VARCHAR(200),
            class_hierarchy TEXT[]
        );
        CREATE INDEX IF NOT EXISTS idx_classes_antibiotic ON snomed_drug_classes(is_antibiotic) WHERE is_antibiotic;
        CREATE INDEX IF NOT EXISTS idx_classes_analgesic ON snomed_drug_classes(is_analgesic) WHERE is_analgesic;
    """)
    
    conn.commit()
    cursor.close()
    logger.info("Extended tables created")

def load_relationships(conn):
    """Load drug hierarchies (IS-A relationships)"""
    logger.info("Loading drug relationships...")
    
    file_path = RF2_DIR / "Terminology" / "sct2_Relationship_Snapshot_IN1000189_20251219T120000Z.txt"
    
    cursor = conn.cursor()
    batch = []
    count = 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        
        for row in reader:
            if row['active'] == '1' and row['typeId'] == '116680003':  # IS-A relationship
                batch.append((
                    int(row['sourceId']),
                    int(row['destinationId']),
                    'IS-A',
                    True
                ))
                
                if len(batch) >= 5000:
                    execute_batch(cursor, """
                        INSERT INTO snomed_drug_hierarchy (drug_id, parent_id, relationship_type, active)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (drug_id, parent_id) DO NOTHING
                    """, batch)
                    count += len(batch)
                    batch = []
        
        if batch:
            execute_batch(cursor, """
                INSERT INTO snomed_drug_hierarchy (drug_id, parent_id, relationship_type, active)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (drug_id, parent_id) DO NOTHING
            """, batch)
            count += len(batch)
    
    conn.commit()
    cursor.close()
    logger.info(f"Loaded {count:,} relationships")

def load_definitions(conn):
    """Load clinical definitions"""
    logger.info("Loading clinical definitions...")
    
    file_path = RF2_DIR / "Terminology" / "sct2_TextDefinition_Snapshot-en_IN1000189_20251219T120000Z.txt"
    
    if not file_path.exists():
        logger.warning("Text definitions file not found, skipping...")
        return
    
    cursor = conn.cursor()
    batch = []
    count = 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        
        for row in reader:
            if row['active'] == '1':
                batch.append((
                    int(row['conceptId']),
                    row['term'],
                    row['languageCode']
                ))
                
                if len(batch) >= 5000:
                    execute_batch(cursor, """
                        INSERT INTO snomed_drug_definitions (drug_id, definition, language_code)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (drug_id) DO UPDATE SET definition = EXCLUDED.definition
                    """, batch)
                    count += len(batch)
                    batch = []
        
        if batch:
            execute_batch(cursor, """
                INSERT INTO snomed_drug_definitions (drug_id, definition, language_code)
                VALUES (%s, %s, %s)
                ON CONFLICT (drug_id) DO UPDATE SET definition = EXCLUDED.definition
            """, batch)
            count += len(batch)
    
    conn.commit()
    cursor.close()
    logger.info(f"Loaded {count:,} definitions")

def load_dosages(conn):
    """Load precise dosage information"""
    logger.info("Loading dosage information...")
    
    file_path = RF2_DIR / "Terminology" / "sct2_RelationshipConcreteValues_Snapshot_IN1000189_20251219T120000Z.txt"
    
    cursor = conn.cursor()
    batch = []
    count = 0
    
    # Attribute type mapping
    attr_map = {
        '1142138002': 'strength_numerator',
        '1142139005': 'strength_denominator',
        '1142136003': 'concentration_numerator',
        '1142137007': 'concentration_denominator'
    }
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        
        for row in reader:
            if row['active'] == '1':
                attr_type = attr_map.get(row['typeId'], 'other')
                value = row['value'].replace('#', '').strip()
                
                try:
                    value_numeric = float(value)
                    value_text = None
                except:
                    value_numeric = None
                    value_text = value
                
                batch.append((
                    int(row['sourceId']),
                    attr_type,
                    value_numeric,
                    value_text,
                    None
                ))
                
                if len(batch) >= 5000:
                    execute_batch(cursor, """
                        INSERT INTO snomed_drug_dosages (drug_id, attribute_type, value_numeric, value_text, unit_code)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (drug_id, attribute_type) DO UPDATE SET 
                            value_numeric = EXCLUDED.value_numeric,
                            value_text = EXCLUDED.value_text
                    """, batch)
                    count += len(batch)
                    batch = []
        
        if batch:
            execute_batch(cursor, """
                INSERT INTO snomed_drug_dosages (drug_id, attribute_type, value_numeric, value_text, unit_code)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (drug_id, attribute_type) DO UPDATE SET 
                    value_numeric = EXCLUDED.value_numeric,
                    value_text = EXCLUDED.value_text
            """, batch)
            count += len(batch)
    
    conn.commit()
    cursor.close()
    logger.info(f"Loaded {count:,} dosage records")

def classify_drugs(conn):
    """Classify drugs based on hierarchy (antibiotics, analgesics, etc.)"""
    logger.info("Classifying drugs...")
    
    cursor = conn.cursor()
    
    # Known SNOMED codes for drug classes
    drug_classes = {
        'antibiotic': [419382002, 372687004],  # Antibacterial, Antibiotic
        'analgesic': [373265006, 372665008],   # Analgesic, Opioid analgesic
        'antihypertensive': [372586001],       # Antihypertensive
        'antidiabetic': [372448005],           # Antidiabetic
        'antiinflammatory': [330901000]        # Anti-inflammatory
    }
    
    # Build classification
    cursor.execute("""
        INSERT INTO snomed_drug_classes (drug_id, drug_name)
        SELECT DISTINCT b.snomed_id, b.brand_name
        FROM snomed_brands b
        ON CONFLICT (drug_id) DO UPDATE SET drug_name = EXCLUDED.drug_name
    """)
    
    # Mark antibiotics
    for class_name, codes in drug_classes.items():
        for code in codes:
            cursor.execute(f"""
                WITH RECURSIVE drug_tree AS (
                    SELECT drug_id, parent_id FROM snomed_drug_hierarchy WHERE parent_id = %s
                    UNION ALL
                    SELECT h.drug_id, h.parent_id 
                    FROM snomed_drug_hierarchy h
                    JOIN drug_tree dt ON h.parent_id = dt.drug_id
                )
                UPDATE snomed_drug_classes
                SET is_{class_name} = TRUE,
                    drug_class = COALESCE(drug_class, %s)
                WHERE drug_id IN (SELECT drug_id FROM drug_tree)
            """, (code, class_name.title()))
    
    conn.commit()
    cursor.close()
    logger.info("Drug classification completed")

def main():
    logger.info("=" * 80)
    logger.info("SNOMED CT RF2 Extended Data Loader")
    logger.info("=" * 80)
    
    conn = get_db_connection()
    
    try:
        create_extended_tables(conn)
        load_relationships(conn)
        load_definitions(conn)
        load_dosages(conn)
        classify_drugs(conn)
        
        logger.info("=" * 80)
        logger.info("RF2 Extended Data Loaded Successfully!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    main()
