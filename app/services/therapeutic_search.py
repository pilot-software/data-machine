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


def get_drugs_for_symptoms(db, symptoms: List[str], diagnosis: str = "", icd_codes: List[str] = [], llm_generic_drugs: List[str] = []) -> List[Dict]:
    """
    Get drugs using database indication/therapeutic_role fields
    Priority: LLM generic drugs > Database indication search > Diagnosis search
    """
    drugs = []
    
    # PRIORITY 1: Use LLM's generic drug suggestions (most accurate)
    if llm_generic_drugs:
        logger.info(f"Searching database for LLM drugs: {llm_generic_drugs}")
        for generic in llm_generic_drugs[:6]:
            # Extract drug names
            drug_terms = [generic.lower()]
            if "(" in generic:
                import re
                matches = re.findall(r'\b([a-z]{4,}(?:cillin|mycin|floxacin|azole|prim|furantoin|cycline|ambutol|niazid|ampicin|idone))\b', generic.lower())
                drug_terms.extend(matches)
            
            for term in drug_terms:
                query = text("""
                    SELECT DISTINCT b.snomed_id, b.brand_name, g.generic_name, s.supplier_name,
                           g.indication, g.therapeutic_role
                    FROM snomed_brands b
                    JOIN snomed_generics g ON b.generic_id = g.snomed_id
                    LEFT JOIN snomed_suppliers s ON b.supplier_id = s.snomed_id
                    WHERE LOWER(g.generic_name) LIKE :term
                      AND b.active = TRUE
                      AND b.route_of_administration = 'oral'
                    LIMIT 2
                """)
                results = db.execute(query, {"term": f"%{term}%"}).fetchall()
                for row in results:
                    drugs.append(dict(row._mapping))
                if results:
                    break
        
        if drugs:
            logger.info(f"Found {len(drugs)} drugs from LLM suggestions")
            return drugs[:6]
    
    # PRIORITY 2: Search database by diagnosis/condition
    if diagnosis:
        logger.info(f"Searching database for diagnosis: {diagnosis}")
        query = text("""
            SELECT DISTINCT b.snomed_id, b.brand_name, g.generic_name, s.supplier_name,
                   g.indication, g.therapeutic_role
            FROM snomed_brands b
            JOIN snomed_generics g ON b.generic_id = g.snomed_id
            LEFT JOIN snomed_suppliers s ON b.supplier_id = s.snomed_id
            WHERE (LOWER(g.indication) LIKE :diagnosis
               OR LOWER(g.therapeutic_role) LIKE :diagnosis)
              AND b.active = TRUE
              AND b.route_of_administration = 'oral'
            LIMIT 6
        """)
        results = db.execute(query, {"diagnosis": f"%{diagnosis.lower()}%"}).fetchall()
        for row in results:
            drugs.append(dict(row._mapping))
        
        if drugs:
            logger.info(f"Found {len(drugs)} drugs for diagnosis")
            return drugs[:6]
    
    # PRIORITY 3: Search by symptoms
    if symptoms:
        logger.info(f"Searching database for symptoms: {symptoms}")
        for symptom in symptoms[:3]:
            query = text("""
                SELECT DISTINCT b.snomed_id, b.brand_name, g.generic_name, s.supplier_name,
                       g.indication, g.therapeutic_role
                FROM snomed_brands b
                JOIN snomed_generics g ON b.generic_id = g.snomed_id
                LEFT JOIN snomed_suppliers s ON b.supplier_id = s.snomed_id
                WHERE (LOWER(g.indication) LIKE :symptom
                   OR LOWER(g.therapeutic_role) LIKE :symptom)
                  AND b.active = TRUE
                  AND b.route_of_administration = 'oral'
                LIMIT 2
            """)
            results = db.execute(query, {"symptom": f"%{symptom.lower()}%"}).fetchall()
            for row in results:
                drugs.append(dict(row._mapping))
    
    # Remove duplicates
    seen = set()
    unique = []
    for d in drugs:
        if d['snomed_id'] not in seen:
            seen.add(d['snomed_id'])
            unique.append(d)
    
    return unique[:6]
