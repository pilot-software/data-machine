"""
RxNorm API Integration for Drug Safety
Free NIH API - No API key required
"""

import requests
from typing import List, Dict
from sqlalchemy import text

RXNORM_BASE = "https://rxnav.nlm.nih.gov/REST"


def get_rxcui(drug_name: str) -> str:
    """Get RxNorm Concept Unique Identifier"""
    try:
        response = requests.get(
            f"{RXNORM_BASE}/rxcui.json",
            params={"name": drug_name, "search": 1},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("idGroup", {}).get("rxnormId"):
                return data["idGroup"]["rxnormId"][0]
    except:
        pass
    return None


def get_drug_interactions(rxcui_list: List[str]) -> List[Dict]:
    """Get drug-drug interactions from RxNorm"""
    if not rxcui_list:
        return []
    
    try:
        rxcuis = "+".join(rxcui_list)
        response = requests.get(
            f"{RXNORM_BASE}/interaction/list.json",
            params={"rxcuis": rxcuis},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            interactions = []
            
            for group in data.get("fullInteractionTypeGroup", []):
                for interaction in group.get("fullInteractionType", []):
                    for pair in interaction.get("interactionPair", []):
                        interactions.append({
                            "drug1": pair.get("interactionConcept", [{}])[0].get("minConceptItem", {}).get("name"),
                            "drug2": pair.get("interactionConcept", [{}])[1].get("minConceptItem", {}).get("name"),
                            "severity": pair.get("severity", "unknown"),
                            "description": pair.get("description", "")
                        })
            
            return interactions
    except:
        pass
    
    return []


def get_drug_properties(rxcui: str) -> Dict:
    """Get drug properties including dosing info from RxNorm"""
    try:
        response = requests.get(
            f"{RXNORM_BASE}/rxcui/{rxcui}/property.json",
            params={"propName": "all"},
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("propConceptGroup", {}).get("propConcept", [])
    except:
        pass
    return []


def get_snomed_drug_metadata(snomed_id: int, db) -> Dict:
    """Get drug metadata from SNOMED CT database"""
    try:
        result = db.execute(text("""
            SELECT typeId, value 
            FROM snomed_concrete_values 
            WHERE sourceId = :snomed_id AND active = 1
        """), {"snomed_id": snomed_id}).fetchall()
        
        metadata = {}
        for row in result:
            if row.typeId in [1142138002, 1142139005]:
                metadata["strength"] = row.value.replace("#", "")
        
        return metadata
    except Exception:
        db.rollback()
        return {}


def validate_drugs_with_rxnorm(drugs: List[Dict], patient_age: int, diagnosis: str, db=None) -> Dict:
    """
    Validate drugs using RxNorm API
    Returns: {"safe_drugs": [], "warnings": [], "interactions": []}
    """
    warnings = []
    interactions = []
    rxcui_map = {}
    
    # Dosing limits (WHO/FDA guidelines)
    DOSE_LIMITS = {
        "paracetamol": {"max_single": 1000, "max_daily": 4000, "unit": "mg"},
        "acetaminophen": {"max_single": 1000, "max_daily": 4000, "unit": "mg"},
        "ibuprofen": {"max_single": 400, "max_daily": 2400, "unit": "mg"},
        "aspirin": {"max_single": 1000, "max_daily": 4000, "unit": "mg", "min_age": 12},
        "naproxen": {"max_single": 500, "max_daily": 1250, "unit": "mg"},
        "diclofenac": {"max_single": 50, "max_daily": 150, "unit": "mg"},
    }
    
    # Get RxCUIs for all drugs
    for drug in drugs:
        generic = drug.get("generic_name", "").split()[0].lower()
        rxcui = get_rxcui(generic)
        if rxcui:
            rxcui_map[generic] = rxcui
            
            # Check SNOMED metadata if database available
            if db and drug.get("snomed_id"):
                try:
                    snomed_meta = get_snomed_drug_metadata(drug["snomed_id"], db)
                    if snomed_meta.get("strength"):
                        dose = float(snomed_meta["strength"])
                        if generic in DOSE_LIMITS:
                            limits = DOSE_LIMITS[generic]
                            if dose > limits["max_single"]:
                                warnings.append(f"❌ {drug['brand_name']}: SNOMED strength {dose}mg exceeds max {limits['max_single']}mg")
                except Exception:
                    pass
            
            # Check dosing from brand name (extract mg if present)
            brand = drug.get("brand_name", "")
            import re
            dose_match = re.search(r'(\d+)\s*mg', brand.lower())
            
            if dose_match and generic in DOSE_LIMITS:
                dose = int(dose_match.group(1))
                limits = DOSE_LIMITS[generic]
                
                if dose > limits["max_single"]:
                    warnings.append(f"❌ {drug['brand_name']}: Dose {dose}mg exceeds max single dose {limits['max_single']}mg")
                
                if "min_age" in limits and patient_age < limits["min_age"]:
                    warnings.append(f"❌ {generic.title()}: CONTRAINDICATED for age {patient_age} (min age: {limits['min_age']} years)")
    
    # Check drug-drug interactions
    if len(rxcui_map) > 1:
        rxcui_list = list(rxcui_map.values())
        drug_interactions = get_drug_interactions(rxcui_list)
        
        for interaction in drug_interactions:
            severity = interaction.get("severity", "").lower()
            if severity in ["high", "severe"]:
                warnings.append(f"⚠️ INTERACTION: {interaction['drug1']} + {interaction['drug2']} - {interaction['description']}")
            interactions.append(interaction)
    
    return {
        "safe_drugs": drugs,  # RxNorm doesn't filter, just warns
        "warnings": warnings,
        "interactions": interactions
    }
