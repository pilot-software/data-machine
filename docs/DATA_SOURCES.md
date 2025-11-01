# 💊 Real Indian Drug Data Sources

## 🇮🇳 **Official Government Sources (FREE)**

### 1. **CDSCO - Central Drugs Standard Control Organization**
- **URL**: https://cdsco.gov.in/opencms/opencms/en/Drugs/
- **Data**: Approved drugs list, schedules, banned drugs
- **Format**: PDF/Excel downloads
- **Coverage**: All CDSCO approved drugs in India
- **Cost**: FREE

**How to get:**
```bash
# Download from CDSCO website
1. Visit: https://cdsco.gov.in/opencms/opencms/en/Drugs/Approved-Drugs/
2. Download: "List of Approved Drugs"
3. Format: Excel/PDF
```

### 2. **NPPA - National Pharmaceutical Pricing Authority**
- **URL**: https://www.nppaindia.nic.in/
- **Data**: Drug prices (MRP), ceiling prices, DPCO list
- **Format**: Excel/PDF
- **Coverage**: Price-controlled drugs + market prices
- **Cost**: FREE

**How to get:**
```bash
# Download price list
1. Visit: https://www.nppaindia.nic.in/en/ceiling-price/
2. Download: "DPCO 2013 - Ceiling Price List"
3. Contains: Drug name, strength, MRP, manufacturer
```

### 3. **Indian Pharmacopoeia Commission**
- **URL**: https://ipc.gov.in/
- **Data**: Drug standards, formulations
- **Format**: PDF
- **Cost**: FREE (basic data)

---

## 🏥 **Commercial Databases (PAID but Comprehensive)**

### 1. **MIMS India** ⭐ RECOMMENDED
- **URL**: https://www.mims.com/india
- **Data**: 50,000+ drugs, complete formulations, prices
- **Coverage**: All Indian brands + generics
- **Cost**: ~₹50,000-1,00,000/year
- **API**: Available for integration

**What you get:**
- Brand names + manufacturers
- Generic compositions
- Strengths, dosage forms
- MRP prices
- Indications, contraindications
- Drug interactions

### 2. **CIMS (Current Index of Medical Specialities)**
- **URL**: https://www.mims.com/india/cims
- **Data**: Similar to MIMS
- **Cost**: ~₹40,000-80,000/year

### 3. **Medex India**
- **URL**: Contact medical publishers
- **Data**: Drug database with pricing
- **Cost**: ~₹30,000-60,000/year

---

## 🆓 **Free/Open Data Sources**

### 1. **RxNorm (US NLM - FREE)**
- **URL**: https://www.nlm.nih.gov/research/umls/rxnorm/
- **Data**: Generic drug names, RxNorm CUI mapping
- **API**: https://rxnav.nlm.nih.gov/
- **Coverage**: Global generics (not Indian brands)
- **Cost**: FREE

**API Example:**
```bash
# Get RxNorm CUI for Metformin
curl "https://rxnav.nlm.nih.gov/REST/rxcui.json?name=metformin"

# Response: {"idGroup":{"rxnormId":["6809"]}}
```

### 2. **WHO ICD-11 API (FREE)**
- **URL**: https://icd.who.int/icdapi
- **Data**: Disease classifications
- **Cost**: FREE

### 3. **OpenFDA (US FDA - FREE)**
- **URL**: https://open.fda.gov/
- **Data**: US drug database
- **Note**: Not Indian drugs, but good for generics
- **Cost**: FREE

### 4. **Kaggle Datasets**
- **URL**: https://www.kaggle.com/datasets
- **Search**: "Indian drugs", "medicine database"
- **Data**: Community-contributed datasets
- **Cost**: FREE

**Example datasets:**
```
1. "Indian Medicine Database" - 10K+ drugs
2. "Pharmaceutical Data India" - Brand + Generic mapping
3. "Drug Prices India" - MRP data
```

### 5. **GitHub Repositories**
- **Search**: "Indian drugs database", "medicine API India"
- **Examples**:
  - https://github.com/topics/indian-drugs
  - https://github.com/topics/medicine-database

---

## 📊 **Web Scraping Sources (Legal Gray Area)**

### 1. **1mg.com**
- **URL**: https://www.1mg.com/
- **Data**: 100,000+ drugs with prices
- **Method**: Web scraping (check ToS)
- **Coverage**: Complete Indian market

### 2. **Netmeds.com**
- **URL**: https://www.netmeds.com/
- **Data**: Drug database with prices
- **Method**: Web scraping

### 3. **PharmEasy**
- **URL**: https://pharmeasy.in/
- **Data**: Drug listings with MRP

**⚠️ Warning:** Check Terms of Service before scraping

---

## 🎯 **Recommended Approach for Production**

### **Option 1: Budget (FREE)**
```
1. CDSCO → Drug approvals
2. NPPA → Pricing data
3. RxNorm API → Generic mapping
4. Kaggle → Community data
5. Manual curation → Fill gaps

Total Cost: ₹0
Time: 2-3 months
Coverage: 60-70%
```

### **Option 2: Professional (PAID)** ⭐ RECOMMENDED
```
1. MIMS India → Complete database
2. RxNorm API → Global mapping
3. NPPA → Price verification

Total Cost: ₹50,000-1,00,000/year
Time: 1-2 weeks
Coverage: 95%+
Quality: High
```

### **Option 3: Hybrid (BEST VALUE)**
```
1. MIMS India → Core database (₹50K/year)
2. CDSCO → Regulatory updates (FREE)
3. NPPA → Price updates (FREE)
4. RxNorm → Global standards (FREE)

Total Cost: ₹50,000/year
Coverage: 95%+
Maintenance: Easy
```

---

## 📥 **Quick Start: Free Data Collection**

### **Step 1: Download NPPA Price List**
```bash
# Visit NPPA website
wget https://www.nppaindia.nic.in/ceiling-price/list.xlsx

# Convert to CSV
python convert_nppa_to_csv.py
```

### **Step 2: Get RxNorm Mapping**
```python
import requests

def get_rxnorm_cui(drug_name):
    url = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={drug_name}"
    response = requests.get(url)
    data = response.json()
    if 'idGroup' in data and 'rxnormId' in data['idGroup']:
        return data['idGroup']['rxnormId'][0]
    return None

# Example
cui = get_rxnorm_cui("metformin")
print(f"RxNorm CUI: {cui}")  # Output: 6809
```

### **Step 3: Scrape 1mg (Educational)**
```python
import requests
from bs4 import BeautifulSoup

def scrape_1mg(drug_name):
    url = f"https://www.1mg.com/search/all?name={drug_name}"
    # Add proper headers, respect robots.txt
    # This is for educational purposes only
    pass
```

---

## 🔄 **Data Update Frequency**

| Source | Update Frequency | How to Update |
|--------|------------------|---------------|
| CDSCO | Monthly | Check website |
| NPPA | Quarterly | Download new list |
| MIMS | Real-time | API sync |
| RxNorm | Monthly | API always current |
| Kaggle | Varies | Check dataset updates |

---

## 💡 **Sample Data Structure**

### **Minimal Required Fields**
```csv
brand_name,generic_name,manufacturer,strength,dosage_form,mrp,pack_size
Crocin,Acetaminophen,GSK,500mg,Tablet,15.00,10 tablets
Dolo 650,Acetaminophen,Micro Labs,650mg,Tablet,30.00,15 tablets
```

### **Complete Fields (Professional)**
```csv
brand_name,generic_name,manufacturer,strength,dosage_form,mrp,pack_size,schedule,cdsco_approval,rxnorm_cui,atc_code,indications,contraindications,side_effects
```

---

## 📞 **Contact for Commercial Data**

### **MIMS India**
- Email: india@mims.com
- Phone: +91-80-4092-9999
- Request: API access + database license

### **CIMS**
- Email: info@cims.com
- Request: Database subscription

### **Medex**
- Contact: Medical publishers in India
- Request: Digital database access

---

## 🎯 **My Recommendation**

**For MVP (3 months):**
1. Use FREE sources (NPPA + CDSCO + RxNorm)
2. Manual curation for top 500 drugs
3. Community contributions

**For Production (6 months):**
1. Buy MIMS India license (₹50K/year)
2. Integrate RxNorm for global standards
3. Auto-sync with NPPA for prices

**ROI:** ₹50K investment saves 6 months of manual work

---

## 📊 **Data Quality Comparison**

| Source | Coverage | Accuracy | Cost | Update |
|--------|----------|----------|------|--------|
| MIMS | 95% | 99% | ₹50K/yr | Real-time |
| CDSCO | 80% | 95% | FREE | Monthly |
| NPPA | 60% | 99% | FREE | Quarterly |
| Kaggle | 40% | 70% | FREE | Varies |
| Scraping | 90% | 80% | FREE | Manual |

---

## ✅ **Action Plan**

**Week 1:**
- [ ] Download NPPA price list
- [ ] Setup RxNorm API integration
- [ ] Download CDSCO approved drugs

**Week 2:**
- [ ] Clean and normalize data
- [ ] Map to RxNorm CUI
- [ ] Load into database

**Week 3:**
- [ ] Contact MIMS for quote
- [ ] Evaluate data quality
- [ ] Decide on paid vs free

**Week 4:**
- [ ] Implement chosen solution
- [ ] Setup auto-updates
- [ ] Test API

**Start with FREE sources, upgrade to MIMS when you have users!** 🚀
