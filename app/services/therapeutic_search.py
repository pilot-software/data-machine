"""
Drug Search by Therapeutic Role and Indication
Uses existing SNOMED data to find appropriate drugs
"""

from sqlalchemy import text
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def search_by_therapeutic_role(db, role: str, limit: int = 5) -> List[Dict]:
    """Search drugs by therapeutic role"""
    query = text("""
        SELECT DISTINCT b.snomed_id, b.brand_name, g.generic_name, s.supplier_name,
               g.therapeutic_role, g.indication
        FROM snomed_brands b
        JOIN snomed_generics g ON b.generic_id = g.snomed_id
        LEFT JOIN snomed_suppliers s ON b.supplier_id = s.snomed_id
        WHERE LOWER(g.therapeutic_role) LIKE :role
          AND b.active = TRUE
          AND b.route_of_administration = 'oral'
        LIMIT :limit
    """)
    
    results = db.execute(query, {"role": f"%{role.lower()}%", "limit": limit}).fetchall()
    return [dict(row._mapping) for row in results]


def search_by_indication(db, indication: str, limit: int = 5) -> List[Dict]:
    """Search drugs by indication"""
    query = text("""
        SELECT DISTINCT b.snomed_id, b.brand_name, g.generic_name, s.supplier_name,
               g.therapeutic_role, g.indication
        FROM snomed_brands b
        JOIN snomed_generics g ON b.generic_id = g.snomed_id
        LEFT JOIN snomed_suppliers s ON b.supplier_id = s.snomed_id
        WHERE LOWER(g.indication) LIKE :indication
          AND b.active = TRUE
          AND b.route_of_administration = 'oral'
        LIMIT :limit
    """)
    
    results = db.execute(query, {"indication": f"%{indication.lower()}%", "limit": limit}).fetchall()
    return [dict(row._mapping) for row in results]


# Symptom-to-drug mapping for common symptoms
SYMPTOM_DRUG_MAP = {
    'headache': ['paracetamol', 'ibuprofen', 'aspirin'],
    'head ache': ['paracetamol', 'ibuprofen'],
    'pain': ['paracetamol', 'ibuprofen', 'diclofenac'],
    'fever': ['paracetamol', 'ibuprofen'],
    'cough': ['dextromethorphan', 'codeine'],
    'cold': ['cetirizine', 'phenylephrine'],
    'nausea': ['ondansetron', 'domperidone'],
    'vomiting': ['ondansetron', 'domperidone'],
    'diarrhea': ['loperamide', 'racecadotril'],
    'constipation': ['bisacodyl', 'lactulose']
}

def get_drugs_for_symptoms(db, symptoms: List[str], diagnosis: str = "", icd_codes: List[str] = []) -> List[Dict]:
    """
    Get appropriate drugs based on symptoms, diagnosis, and ICD-10 codes
    Uses database indication field and generic name search
    """
    drugs = []
    primary_drugs = []
    symptom_drugs = []
    
    # Try ICD-10 mapping first (most accurate) - for primary diagnosis
    if icd_codes:
        import yaml
        import os
        try:
            config_path = os.path.join(os.path.dirname(__file__), '../../config/icd_ingredient_mapping.yaml')
            with open(config_path, 'r') as f:
                icd_config = yaml.safe_load(f)
                
                for icd_code in icd_codes:
                    normalized = icd_code.replace(".", "")[:3]
                    if normalized in icd_config.get('icd_ingredient_mapping', {}):
                        mapping = icd_config['icd_ingredient_mapping'][normalized]
                        ingredients = mapping.get('ingredients', [])
                        logger.info(f"ICD {normalized} mapped to: {ingredients}")
                        
                        for ingredient in ingredients[:2]:
                            query = text("""
                                SELECT DISTINCT b.snomed_id, b.brand_name, g.generic_name, s.supplier_name
                                FROM snomed_brands b
                                JOIN snomed_generics g ON b.generic_id = g.snomed_id
                                LEFT JOIN snomed_suppliers s ON b.supplier_id = s.snomed_id
                                WHERE LOWER(g.generic_name) LIKE :ingredient
                                  AND b.active = TRUE
                                  AND b.route_of_administration = 'oral'
                                LIMIT 2
                            """)
                            results = db.execute(query, {"ingredient": f"%{ingredient}%"}).fetchall()
                            for row in results:
                                primary_drugs.append(dict(row._mapping))
                        
                        if primary_drugs:
                            break
        except Exception as e:
            logger.warning(f"ICD mapping failed: {e}")
    
    # ALWAYS search for symptom-specific drugs (e.g., headache, pain)
    if symptoms:
        for symptom in symptoms:
            symptom_lower = symptom.lower()
            
            # Try direct generic name search for mapped symptoms
            if symptom_lower in SYMPTOM_DRUG_MAP:
                for generic in SYMPTOM_DRUG_MAP[symptom_lower][:2]:
                    query = text("""
                        SELECT DISTINCT b.snomed_id, b.brand_name, g.generic_name, s.supplier_name,
                               g.indication, g.therapeutic_role
                        FROM snomed_brands b
                        JOIN snomed_generics g ON b.generic_id = g.snomed_id
                        LEFT JOIN snomed_suppliers s ON b.supplier_id = s.snomed_id
                        WHERE LOWER(g.generic_name) LIKE :generic
                          AND b.active = TRUE
                          AND b.route_of_administration = 'oral'
                        LIMIT 1
                    """)
                    results = db.execute(query, {"generic": f"%{generic}%"}).fetchall()
                    for row in results:
                        symptom_drugs.append(dict(row._mapping))
                    if results:
                        logger.info(f"Found {len(results)} drugs for symptom '{symptom}' via generic '{generic}'")
                        break
            
            # Fallback: search by indication/therapeutic role
            if not symptom_drugs:
                query = text("""
                    SELECT DISTINCT b.snomed_id, b.brand_name, g.generic_name, s.supplier_name,
                           g.indication, g.therapeutic_role
                    FROM snomed_brands b
                    JOIN snomed_generics g ON b.generic_id = g.snomed_id
                    LEFT JOIN snomed_suppliers s ON b.supplier_id = s.snomed_id
                    WHERE (LOWER(g.indication) LIKE :term OR LOWER(g.therapeutic_role) LIKE :term)
                      AND b.active = TRUE
                      AND b.route_of_administration = 'oral'
                    LIMIT 1
                """)
                results = db.execute(query, {"term": f"%{symptom_lower}%"}).fetchall()
                for row in results:
                    symptom_drugs.append(dict(row._mapping))
                
                if results:
                    logger.info(f"Found {len(results)} drugs for symptom: {symptom}")
    
    # Combine: primary diagnosis drugs + symptom-specific drugs
    drugs = primary_drugs + symptom_drugs
    
    # Fallback: search by diagnosis if no drugs found
    if not drugs and diagnosis:
        query = text("""
            SELECT DISTINCT b.snomed_id, b.brand_name, g.generic_name, s.supplier_name,
                   g.indication, g.therapeutic_role
            FROM snomed_brands b
            JOIN snomed_generics g ON b.generic_id = g.snomed_id
            LEFT JOIN snomed_suppliers s ON b.supplier_id = s.snomed_id
            WHERE (LOWER(g.indication) LIKE :term OR LOWER(g.therapeutic_role) LIKE :term)
              AND b.active = TRUE
              AND b.route_of_administration = 'oral'
            LIMIT 3
        """)
        results = db.execute(query, {"term": f"%{diagnosis.lower()}%"}).fetchall()
        for row in results:
            drugs.append(dict(row._mapping))
    
    # Remove duplicates
    seen = set()
    unique_drugs = []
    for drug in drugs:
        if drug['snomed_id'] not in seen:
            seen.add(drug['snomed_id'])
            unique_drugs.append(drug)
    
    return unique_drugs[:6]
