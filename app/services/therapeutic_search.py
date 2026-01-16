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


def get_drugs_for_symptoms(db, symptoms: List[str], diagnosis: str = "", icd_codes: List[str] = []) -> List[Dict]:
    """
    Get appropriate drugs based on symptoms, diagnosis, and ICD-10 codes
    Priority: ICD-10 mapping > Symptom mapping > Fallback
    """
    drugs = []
    
    # Try ICD-10 mapping first (most accurate)
    if icd_codes:
        import yaml
        import os
        try:
            config_path = os.path.join(os.path.dirname(__file__), '../../config/icd_ingredient_mapping.yaml')
            with open(config_path, 'r') as f:
                icd_config = yaml.safe_load(f)
                
                for icd_code in icd_codes:
                    # Normalize: J20.9 -> J20
                    normalized = icd_code.replace(".", "")[:3]
                    if normalized in icd_config.get('icd_ingredient_mapping', {}):
                        mapping = icd_config['icd_ingredient_mapping'][normalized]
                        ingredients = mapping.get('ingredients', [])
                        logger.info(f"ICD {normalized} mapped to: {ingredients}")
                        
                        # Search for these ingredients
                        for ingredient in ingredients[:3]:
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
                                drugs.append(dict(row._mapping))
                        
                        if drugs:
                            break  # Found drugs via ICD mapping
        except Exception as e:
            logger.warning(f"ICD mapping failed: {e}")
    
    # Fallback to symptom mapping if no ICD results
    
    # Symptom to drug ingredient mapping (evidence-based, Mumbai high-volume complaints)
    symptom_to_ingredient = {
        # Pain & Fever (most common)
        "pain": ["paracetamol", "ibuprofen", "diclofenac"],
        "headache": ["paracetamol", "ibuprofen"],
        "fever": ["paracetamol", "ibuprofen"],
        "body ache": ["paracetamol", "ibuprofen"],
        "back pain": ["diclofenac", "paracetamol"],
        "joint pain": ["diclofenac", "ibuprofen"],
        "toothache": ["ibuprofen", "paracetamol"],
        
        # Respiratory
        "cough": ["dextromethorphan", "guaifenesin", "bromhexine", "ambroxol"],
        "dry cough": ["dextromethorphan"],
        "wet cough": ["guaifenesin", "ambroxol"],
        "cold": ["cetirizine", "phenylephrine"],
        "sore throat": ["paracetamol", "benzydamine"],
        "nasal congestion": ["phenylephrine", "xylometazoline"],
        
        # Allergies
        "allergy": ["cetirizine", "levocetirizine", "loratadine"],
        "skin rash": ["cetirizine", "loratadine"],
        "itching": ["cetirizine", "hydroxyzine"],
        
        # Gastrointestinal (very common in Mumbai)
        "acidity": ["omeprazole", "pantoprazole", "rabeprazole"],
        "heartburn": ["omeprazole", "ranitidine"],
        "gastritis": ["pantoprazole", "sucralfate"],
        "diarrhea": ["loperamide", "racecadotril"],
        "loose motion": ["loperamide", "racecadotril"],
        "constipation": ["ispaghula", "lactulose"],
        "nausea": ["ondansetron", "domperidone"],
        "vomiting": ["ondansetron", "domperidone"],
        "indigestion": ["pantoprazole", "domperidone"],
        
        # Infections
        "urinary infection": ["nitrofurantoin", "norfloxacin"],
        "uti": ["nitrofurantoin", "ciprofloxacin"],
        
        # Metabolic (chronic conditions)
        "diabetes": ["metformin", "glimepiride"],
        "high blood pressure": ["amlodipine", "telmisartan"],
        "hypertension": ["amlodipine", "atenolol"],
    }
    
    # Search by ingredient name
    for symptom in symptoms:
        symptom_lower = symptom.lower()
        for key, ingredients in symptom_to_ingredient.items():
            if key in symptom_lower:
                for ingredient in ingredients[:2]:  # Top 2 per symptom
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
                        drugs.append(dict(row._mapping))
                    if results:
                        logger.info(f"Found {len(results)} drugs with ingredient: {ingredient}")
                break
    
    # Remove duplicates
    seen = set()
    unique_drugs = []
    for drug in drugs:
        if drug['snomed_id'] not in seen:
            seen.add(drug['snomed_id'])
            unique_drugs.append(drug)
    
    return unique_drugs[:5]
