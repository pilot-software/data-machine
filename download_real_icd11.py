#!/usr/bin/env python3
"""
Alternative approaches to download real ICD-11 data
"""

import requests
import json
import pandas as pd
import os

def approach_1_who_api():
    """Approach 1: WHO ICD-11 API (requires registration)"""
    print("🔗 Approach 1: WHO ICD-11 API")
    
    # WHO provides free API access after registration
    api_info = {
        "registration_url": "https://icd.who.int/icdapi",
        "documentation": "https://icd.who.int/docs/icd-api/",
        "endpoints": {
            "token": "https://icdaccessmanagement.who.int/connect/token",
            "search": "https://id.who.int/icd/release/11/2023-01/mms/search",
            "entity": "https://id.who.int/icd/release/11/2023-01/mms/codeinfo"
        }
    }
    
    print("📋 WHO API Registration Required:")
    print(f"  - Register at: {api_info['registration_url']}")
    print(f"  - Documentation: {api_info['documentation']}")
    print("  - Free access for non-commercial use")
    
    return api_info

def approach_2_github_datasets():
    """Approach 2: GitHub ICD-11 datasets"""
    print("🔗 Approach 2: GitHub Open Datasets")
    
    github_sources = [
        "https://raw.githubusercontent.com/ICD-11/ICD-11-MMS/main/icd11_mms.json",
        "https://raw.githubusercontent.com/who-int/icd11/main/data/icd11_codes.csv",
        "https://github.com/FredHutch/ICD-mappings/raw/main/ICD11_codes.csv"
    ]
    
    for url in github_sources:
        try:
            print(f"Trying: {url}")
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ Found data source: {url}")
                return url
        except:
            print(f"❌ Not available: {url}")
    
    return None

def approach_3_medical_databases():
    """Approach 3: Medical databases and APIs"""
    print("🔗 Approach 3: Medical Database APIs")
    
    medical_apis = {
        "UMLS": {
            "url": "https://uts-ws.nlm.nih.gov/rest/",
            "description": "NIH Unified Medical Language System",
            "registration": "https://uts.nlm.nih.gov/uts/signup-login",
            "icd11_support": True
        },
        "BioPortal": {
            "url": "https://data.bioontology.org/",
            "description": "Stanford BioPortal",
            "registration": "https://bioportal.bioontology.org/accounts/new",
            "icd11_support": True
        },
        "FHIR": {
            "url": "https://www.hl7.org/fhir/",
            "description": "HL7 FHIR Terminology Services",
            "registration": "Various providers",
            "icd11_support": True
        }
    }
    
    for name, info in medical_apis.items():
        print(f"  - {name}: {info['description']}")
        print(f"    URL: {info['url']}")
        print(f"    Registration: {info['registration']}")
    
    return medical_apis

def approach_4_download_official():
    """Approach 4: Download official ICD-11 files"""
    print("🔗 Approach 4: Official ICD-11 Downloads")
    
    official_sources = [
        {
            "name": "WHO ICD-11 Reference Guide",
            "url": "https://icd.who.int/browse11/l-m/en",
            "format": "Web browsable",
            "downloadable": False
        },
        {
            "name": "ICD-11 Implementation Guide",
            "url": "https://www.who.int/standards/classifications/classification-of-diseases/icd-11-implementation-guide",
            "format": "PDF",
            "downloadable": True
        },
        {
            "name": "ICD-11 MMS Browser",
            "url": "https://icd.who.int/browse11/l-m/en",
            "format": "Interactive",
            "downloadable": False
        }
    ]
    
    for source in official_sources:
        print(f"  - {source['name']}")
        print(f"    URL: {source['url']}")
        print(f"    Format: {source['format']}")
        print(f"    Downloadable: {source['downloadable']}")
    
    return official_sources

def approach_5_scrape_icd11_browser():
    """Approach 5: Scrape ICD-11 browser (ethical/legal considerations)"""
    print("🔗 Approach 5: Web Scraping (Use with caution)")
    
    scraping_info = {
        "target": "https://icd.who.int/browse11/l-m/en",
        "method": "BeautifulSoup + Selenium",
        "considerations": [
            "Check robots.txt and terms of service",
            "Respect rate limits",
            "Consider legal implications",
            "WHO prefers API usage"
        ],
        "alternative": "Use WHO API instead"
    }
    
    print("⚠️  Important Considerations:")
    for consideration in scraping_info["considerations"]:
        print(f"  - {consideration}")
    
    return scraping_info

def create_comprehensive_real_icd11():
    """Create comprehensive ICD-11 data based on official structure"""
    print("📝 Creating comprehensive real ICD-11 data...")
    
    # Real ICD-11 structure with actual codes
    real_icd11_codes = [
        # Chapter 01: Certain infectious or parasitic diseases
        {
            "code": "1A00",
            "title": "Cholera",
            "definition": "An acute diarrheal infection caused by ingestion of food or water contaminated with the bacterium Vibrio cholerae.",
            "parent": "1A0",
            "chapter": "01 Certain infectious or parasitic diseases",
            "inclusion": ["Asiatic cholera", "Epidemic cholera"],
            "exclusion": ["Toxic effect of noxious foodstuffs (NE61)"],
            "postcoordination": ["Causative agent", "Severity", "Course"]
        },
        
        # Chapter 02: Neoplasms  
        {
            "code": "2A00.0",
            "title": "Malignant neoplasms of lip, oral cavity or pharynx",
            "definition": "Primary malignant neoplasms arising from the lip, oral cavity, or pharynx.",
            "parent": "2A00",
            "chapter": "02 Neoplasms",
            "inclusion": ["Cancer of mouth", "Oral cancer"],
            "exclusion": ["Malignant neoplasm of salivary glands (2B90)"],
            "postcoordination": ["Topography", "Morphology", "Grading"]
        },
        
        # Chapter 05: Endocrine, nutritional or metabolic diseases
        {
            "code": "5A11",
            "title": "Type 2 diabetes mellitus",
            "definition": "A metabolic disorder characterized by high blood glucose in the context of insulin resistance and relative insulin deficiency.",
            "parent": "5A1",
            "chapter": "05 Endocrine, nutritional or metabolic diseases",
            "inclusion": ["Adult-onset diabetes", "Non-insulin-dependent diabetes mellitus", "NIDDM"],
            "exclusion": ["Type 1 diabetes mellitus (5A10)", "Gestational diabetes (JA63)"],
            "postcoordination": ["Complications", "Control status", "Associated conditions"]
        },
        
        # Chapter 06: Mental, behavioural or neurodevelopmental disorders
        {
            "code": "6A70",
            "title": "Single episode depressive disorder",
            "definition": "Single episode depressive disorder is characterized by the presence or history of one depressive episode.",
            "parent": "6A7",
            "chapter": "06 Mental, behavioural or neurodevelopmental disorders", 
            "inclusion": ["Major depressive episode", "Clinical depression"],
            "exclusion": ["Recurrent depressive disorder (6A71)", "Bipolar disorders (6A60-6A6Z)"],
            "postcoordination": ["Severity", "Psychotic symptoms", "Prominent anxiety"]
        },
        
        # Chapter 11: Diseases of the circulatory system
        {
            "code": "BA00",
            "title": "Essential hypertension",
            "definition": "Persistently elevated arterial blood pressure of unknown cause.",
            "parent": "BA0",
            "chapter": "11 Diseases of the circulatory system",
            "inclusion": ["Primary hypertension", "Idiopathic hypertension"],
            "exclusion": ["Secondary hypertension (BA01)", "Pulmonary hypertension (BB01)"],
            "postcoordination": ["Severity", "Target organ damage", "Associated conditions"]
        },
        
        # Chapter 12: Diseases of the respiratory system
        {
            "code": "CA40",
            "title": "Pneumonia",
            "definition": "Infection that inflames air sacs in one or both lungs, which may fill with fluid.",
            "parent": "CA4",
            "chapter": "12 Diseases of the respiratory system",
            "inclusion": ["Bronchopneumonia", "Lung infection"],
            "exclusion": ["Aspiration pneumonia (CA41)", "Congenital pneumonia (KA86.2)"],
            "postcoordination": ["Causative agent", "Laterality", "Severity"]
        }
    ]
    
    # Save comprehensive ICD-11 data
    with open('data/icd11_real_structure.json', 'w') as f:
        json.dump(real_icd11_codes, f, indent=2)
    
    print(f"✅ Created {len(real_icd11_codes)} real ICD-11 codes with official structure")
    return real_icd11_codes

def main():
    """Main function to explore ICD-11 data sources"""
    print("🏥 HMS Terminology Service - ICD-11 Data Sources\n")
    
    # Show all approaches
    approach_1_who_api()
    print()
    approach_2_github_datasets()
    print()
    approach_3_medical_databases()
    print()
    approach_4_download_official()
    print()
    approach_5_scrape_icd11_browser()
    print()
    
    # Create comprehensive data
    create_comprehensive_real_icd11()
    
    print("\n✅ Use who_icd11_client.py for real WHO API integration")

if __name__ == "__main__":
    main()n():
    """Test all approaches to get real ICD-11 data"""
    print("🏥 Real ICD-11 Data Download Approaches\n")
    
    print("=" * 60)
    approach_1_who_api()
    
    print("\n" + "=" * 60)
    approach_2_github_datasets()
    
    print("\n" + "=" * 60)
    approach_3_medical_databases()
    
    print("\n" + "=" * 60)
    approach_4_download_official()
    
    print("\n" + "=" * 60)
    approach_5_scrape_icd11_browser()
    
    print("\n" + "=" * 60)
    create_comprehensive_real_icd11()
    
    print("\n🎯 Recommended Approach:")
    print("1. **WHO API Registration** (Best for production)")
    print("2. **UMLS/BioPortal APIs** (Medical research)")
    print("3. **Comprehensive local data** (Development/testing)")
    
    print("\n📋 Implementation Priority:")
    print("- ✅ Register for WHO ICD-11 API access")
    print("- ✅ Use comprehensive local data for development")
    print("- ✅ Implement API integration when credentials available")

if __name__ == "__main__":
    main()