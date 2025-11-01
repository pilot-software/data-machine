"""
Download real Indian drug data from free sources
"""

import requests
import pandas as pd
import time
from pathlib import Path

# Create data directory
Path("data/real").mkdir(parents=True, exist_ok=True)

print("🚀 Starting real data collection...\n")

# ============================================
# 1. RxNorm API - Get top 100 generic drugs
# ============================================
print("📦 Step 1: Fetching generic drugs from RxNorm...")

COMMON_GENERICS = [
    "Paracetamol", "Metformin", "Amlodipine", "Atorvastatin", "Omeprazole",
    "Azithromycin", "Amoxicillin", "Ibuprofen", "Aspirin", "Pantoprazole",
    "Telmisartan", "Losartan", "Levothyroxine", "Cetirizine", "Montelukast",
    "Ranitidine", "Domperidone", "Norfloxacin", "Ciprofloxacin", "Glimepiride",
    "Insulin", "Salbutamol", "Atenolol", "Ramipril", "Rosuvastatin",
    "Clopidogrel", "Diclofenac", "Tramadol", "Gabapentin", "Pregabalin",
    "Sertraline", "Fluoxetine", "Alprazolam", "Clonazepam", "Lorazepam",
    "Furosemide", "Spironolactone", "Hydrochlorothiazide", "Bisoprolol", "Carvedilol",
    "Digoxin", "Warfarin", "Rivaroxaban", "Enoxaparin", "Heparin",
    "Prednisolone", "Dexamethasone", "Hydrocortisone", "Methylprednisolone", "Betamethasone"
]

rxnorm_data = []
for generic in COMMON_GENERICS[:20]:  # Start with 20
    try:
        # Get RxNorm CUI
        url = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={generic}"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if 'idGroup' in data and 'rxnormId' in data['idGroup']:
            rxcui = data['idGroup']['rxnormId'][0]
            
            # Get ATC code
            atc_url = f"https://rxnav.nlm.nih.gov/REST/rxclass/class/byRxcui.json?rxcui={rxcui}&relaSource=ATC"
            atc_response = requests.get(atc_url, timeout=5)
            atc_data = atc_response.json()
            
            atc_code = None
            if 'rxclassMinConceptList' in atc_data:
                concepts = atc_data['rxclassMinConceptList'].get('rxclassMinConcept', [])
                if concepts:
                    atc_code = concepts[0].get('classId')
            
            rxnorm_data.append({
                'generic_name': generic,
                'rxnorm_cui': rxcui,
                'atc_code': atc_code
            })
            
            print(f"  ✓ {generic}: RxNorm {rxcui}, ATC {atc_code}")
        
        time.sleep(0.5)  # Rate limiting
        
    except Exception as e:
        print(f"  ✗ {generic}: {e}")

# Save RxNorm data
df_rxnorm = pd.DataFrame(rxnorm_data)
df_rxnorm.to_csv('data/real/rxnorm_generics.csv', index=False)
print(f"\n✅ Saved {len(rxnorm_data)} generics to data/real/rxnorm_generics.csv\n")

# ============================================
# 2. Create Indian brand mapping (manual for now)
# ============================================
print("📦 Step 2: Creating Indian brand database...")

# Common Indian brands (curated list)
indian_brands = [
    # Paracetamol
    {"brand": "Crocin", "generic": "Paracetamol", "manufacturer": "GSK", "strength": "500mg", "form": "Tablet", "mrp": 15},
    {"brand": "Dolo 650", "generic": "Paracetamol", "manufacturer": "Micro Labs", "strength": "650mg", "form": "Tablet", "mrp": 30},
    {"brand": "Calpol", "generic": "Paracetamol", "manufacturer": "GSK", "strength": "250mg/5ml", "form": "Syrup", "mrp": 45},
    
    # Metformin
    {"brand": "Glycomet", "generic": "Metformin", "manufacturer": "USV", "strength": "500mg", "form": "Tablet", "mrp": 25},
    {"brand": "Glucophage", "generic": "Metformin", "manufacturer": "Merck", "strength": "500mg", "form": "Tablet", "mrp": 35},
    
    # Amlodipine
    {"brand": "Amlodac", "generic": "Amlodipine", "manufacturer": "Zydus", "strength": "5mg", "form": "Tablet", "mrp": 18},
    {"brand": "Amlong", "generic": "Amlodipine", "manufacturer": "Micro Labs", "strength": "5mg", "form": "Tablet", "mrp": 20},
    
    # Atorvastatin
    {"brand": "Atorva", "generic": "Atorvastatin", "manufacturer": "Zydus", "strength": "10mg", "form": "Tablet", "mrp": 45},
    {"brand": "Lipitor", "generic": "Atorvastatin", "manufacturer": "Pfizer", "strength": "10mg", "form": "Tablet", "mrp": 120},
    
    # Omeprazole
    {"brand": "Omez", "generic": "Omeprazole", "manufacturer": "Dr Reddy's", "strength": "20mg", "form": "Capsule", "mrp": 35},
    {"brand": "Omeprazole", "generic": "Omeprazole", "manufacturer": "Sun Pharma", "strength": "20mg", "form": "Capsule", "mrp": 30},
]

df_brands = pd.DataFrame(indian_brands)
df_brands.to_csv('data/real/indian_brands.csv', index=False)
print(f"✅ Saved {len(indian_brands)} brands to data/real/indian_brands.csv\n")

# ============================================
# 3. Create indications mapping
# ============================================
print("📦 Step 3: Creating indications database...")

indications = [
    {"generic": "Paracetamol", "indications": "fever|pain|headache", "symptoms": "fever|headache|body pain|toothache"},
    {"generic": "Metformin", "indications": "diabetes|blood sugar", "symptoms": "high blood sugar|frequent urination|excessive thirst"},
    {"generic": "Amlodipine", "indications": "hypertension|blood pressure", "symptoms": "high BP|chest pain"},
    {"generic": "Atorvastatin", "indications": "cholesterol|heart", "symptoms": "high cholesterol"},
    {"generic": "Omeprazole", "indications": "acidity|heartburn|ulcer", "symptoms": "acidity|heartburn|stomach pain|acid reflux"},
]

df_indications = pd.DataFrame(indications)
df_indications.to_csv('data/real/drug_indications.csv', index=False)
print(f"✅ Saved {len(indications)} indications to data/real/drug_indications.csv\n")

# ============================================
# Summary
# ============================================
print("=" * 60)
print("📊 DATA COLLECTION SUMMARY")
print("=" * 60)
print(f"✅ RxNorm Generics: {len(rxnorm_data)} drugs")
print(f"✅ Indian Brands: {len(indian_brands)} brands")
print(f"✅ Indications: {len(indications)} mappings")
print("\n📁 Files created:")
print("  - data/real/rxnorm_generics.csv")
print("  - data/real/indian_brands.csv")
print("  - data/real/drug_indications.csv")
print("\n🎯 Next steps:")
print("  1. Run: python load_real_data.py")
print("  2. Test: curl 'http://localhost:8001/api/v1/drugs/search?q=crocin'")
print("\n💡 To get more data:")
print("  - Download NPPA price list from: https://www.nppaindia.nic.in/")
print("  - Or buy MIMS India license for 50K+ drugs")
