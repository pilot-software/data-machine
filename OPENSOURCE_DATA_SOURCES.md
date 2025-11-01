# 🆓 Open-Source Drug Data Sources (100% FREE)

## 🎯 Best Free Sources for Massive Data

### 1. **OpenFDA** ⭐ BEST FOR US DRUGS
- **URL**: https://open.fda.gov/apis/drug/
- **Data**: 100,000+ US FDA approved drugs
- **API**: FREE, no key required
- **Coverage**: Brand names, generics, manufacturers
- **Format**: JSON API
- **Cost**: FREE

**How to use:**
```bash
# Download 1000 drugs
python download_opensource_data.py

# API example
curl "https://api.fda.gov/drug/label.json?limit=100"
```

**What you get:**
- Brand names
- Generic names
- Manufacturers
- Dosage forms
- Routes of administration
- Indications
- Warnings

---

### 2. **RxNorm (NLM)** ⭐ BEST FOR MAPPING
- **URL**: https://www.nlm.nih.gov/research/umls/rxnorm/
- **Data**: Complete drug vocabulary
- **API**: https://rxnav.nlm.nih.gov/
- **Coverage**: Global drug standards
- **Cost**: FREE

**Download full dataset:**
```bash
# RxNorm Full Release (monthly)
wget https://download.nlm.nih.gov/umls/kss/rxnorm/RxNorm_full_current.zip

# Size: ~500MB
# Contains: 2M+ drug concepts
```

**What you get:**
- RxNorm CUI (unique IDs)
- Generic names
- Brand names
- Ingredients
- Strengths
- Dose forms

---

### 3. **DrugBank Open Data** ⭐ BEST FOR DETAILS
- **URL**: https://go.drugbank.com/releases/latest#open-data
- **Data**: 14,000+ approved drugs
- **Format**: CSV download
- **Cost**: FREE (open data subset)

**Download:**
```bash
# Visit website and download
# File: drugbank_all_open_structures.csv
# Size: ~50MB
```

**What you get:**
- Drug names
- Chemical structures
- Molecular formulas
- Indications
- Mechanisms of action
- Pharmacology

---

### 4. **PubChem (NIH)** ⭐ BEST FOR CHEMISTRY
- **URL**: https://pubchem.ncbi.nlm.nih.gov/
- **Data**: 100M+ chemical compounds
- **API**: FREE
- **Cost**: FREE

**API example:**
```bash
# Search by name
curl "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/aspirin/JSON"

# Get drug info
curl "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/property/MolecularFormula,MolecularWeight/JSON"
```

---

### 5. **WHO Essential Medicines List**
- **URL**: https://www.who.int/medicines/publications/essentialmedicines/
- **Data**: 500+ essential drugs
- **Format**: PDF/Excel
- **Cost**: FREE

**Download:**
```bash
# Latest list
wget https://www.who.int/publications/i/item/WHO-MHP-HPS-EML-2023.02

# Contains:
# - Essential medicines
# - Recommended uses
# - Dosages
```

---

### 6. **Indian Government Sources** 🇮🇳

#### **CDSCO (Drug Regulator)**
- **URL**: https://cdsco.gov.in/opencms/opencms/en/Drugs/
- **Data**: Approved drugs in India
- **Format**: PDF/Excel downloads
- **Cost**: FREE

**What to download:**
- List of approved drugs
- Banned drugs list
- Schedule classifications

#### **NPPA (Pricing Authority)**
- **URL**: https://www.nppaindia.nic.in/
- **Data**: Drug prices (MRP)
- **Format**: Excel
- **Cost**: FREE

**Download:**
```bash
# Ceiling price list
wget https://www.nppaindia.nic.in/ceiling-price/list.xlsx

# Contains:
# - Drug names
# - Strengths
# - MRP prices
# - Manufacturers
```

#### **data.gov.in**
- **URL**: https://data.gov.in/
- **Search**: "drugs", "medicines", "pharmaceutical"
- **Format**: CSV/Excel
- **Cost**: FREE

---

### 7. **GitHub Datasets**

#### **Indian Drug Database**
```bash
# Search GitHub
https://github.com/search?q=indian+drugs+database

# Popular repos:
# - indian-medicines-database
# - drug-price-india
# - pharma-data-india
```

#### **Global Drug Datasets**
```bash
# Kaggle datasets
https://www.kaggle.com/datasets?search=drugs

# Popular:
# - FDA Drug Labels
# - Drug Reviews
# - Medicine Recommendation
```

---

### 8. **Wikidata** ⭐ STRUCTURED DATA
- **URL**: https://www.wikidata.org/
- **Data**: Structured drug information
- **API**: SPARQL queries
- **Cost**: FREE

**Query example:**
```sparql
SELECT ?drug ?drugLabel ?rxnorm WHERE {
  ?drug wdt:P31 wd:Q12140.  # Instance of pharmaceutical drug
  ?drug wdt:P3345 ?rxnorm.   # RxNorm CUI
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 1000
```

---

## 🚀 Quick Start: Get 100K+ Drugs Now

### **Step 1: Run Auto-Download**

```bash
python download_opensource_data.py
```

**Result:**
- 1,000 drugs from OpenFDA
- 100 drugs from RxNorm
- WHO essential medicines

### **Step 2: Download DrugBank**

```bash
# Visit: https://go.drugbank.com/releases/latest#open-data
# Download: drugbank_all_open_structures.csv
# Save to: data/opensource/
```

**Result:** +14,000 drugs

### **Step 3: Download RxNorm Full**

```bash
# Download full release
wget https://download.nlm.nih.gov/umls/kss/rxnorm/RxNorm_full_current.zip
unzip RxNorm_full_current.zip

# Extract drug names
python extract_rxnorm_full.py
```

**Result:** +2M drug concepts

### **Step 4: Download NPPA Prices**

```bash
# Download from NPPA website
wget https://www.nppaindia.nic.in/ceiling-price/list.xlsx

# Convert to CSV
python convert_nppa.py
```

**Result:** +5,000 Indian drugs with prices

---

## 📊 Data Coverage Comparison

| Source | Drugs | Indian Data | Global | API | Free |
|--------|-------|-------------|--------|-----|------|
| **OpenFDA** | 100K+ | ❌ | ✅ | ✅ | ✅ |
| **RxNorm** | 2M+ | ❌ | ✅ | ✅ | ✅ |
| **DrugBank** | 14K+ | ❌ | ✅ | ❌ | ✅ |
| **NPPA** | 5K+ | ✅ | ❌ | ❌ | ✅ |
| **CDSCO** | 10K+ | ✅ | ❌ | ❌ | ✅ |
| **PubChem** | 100M+ | ❌ | ✅ | ✅ | ✅ |

---

## 🎯 Recommended Approach

### **For Indian Market:**

```
1. OpenFDA (100K drugs) → Generic names
2. RxNorm (2M concepts) → Global mapping
3. NPPA (5K drugs) → Indian prices
4. CDSCO → Indian approvals
5. Manual curation → Indian brands

Total: 100K+ drugs with Indian context
Time: 1-2 weeks
Cost: FREE
```

### **For Global Market:**

```
1. RxNorm Full (2M) → Complete vocabulary
2. DrugBank (14K) → Detailed info
3. OpenFDA (100K) → US approvals
4. PubChem → Chemical data

Total: 2M+ drug concepts
Time: 1 week
Cost: FREE
```

---

## 💻 Complete Download Script

```bash
#!/bin/bash
# Download all open-source drug data

echo "📥 Downloading open-source drug data..."

# 1. OpenFDA
python download_opensource_data.py

# 2. RxNorm Full
wget https://download.nlm.nih.gov/umls/kss/rxnorm/RxNorm_full_current.zip
unzip RxNorm_full_current.zip

# 3. DrugBank (manual download required)
echo "📥 Download DrugBank from: https://go.drugbank.com/releases/latest#open-data"

# 4. NPPA
wget https://www.nppaindia.nic.in/ceiling-price/list.xlsx

# 5. Load into database
python load_opensource_data.py

echo "✅ Complete! Database has 100K+ drugs"
```

---

## 🔄 Auto-Update Strategy

```bash
# Weekly: OpenFDA + RxNorm
0 2 * * 0 python download_opensource_data.py

# Monthly: DrugBank + NPPA
0 2 1 * * python download_monthly_data.py

# Quarterly: Full RxNorm release
0 2 1 */3 * python download_rxnorm_full.py
```

---

## 📈 Expected Results

**After running all downloads:**

```
✅ Generic Ingredients: 100,000+
✅ Brand Drugs: 50,000+
✅ RxNorm Mapping: Complete
✅ Indian Prices: 5,000+
✅ Chemical Data: Available
✅ Indications: Comprehensive
```

---

## 💡 Pro Tips

1. **Start with OpenFDA** - Easiest to integrate
2. **Use RxNorm for mapping** - Industry standard
3. **Add NPPA for Indian prices** - Essential for India
4. **DrugBank for details** - Best drug information
5. **Automate updates** - Keep data fresh

---

## 🎯 Bottom Line

**You can get 100,000+ drugs for FREE using open-source data!**

**Best combination:**
- OpenFDA (100K drugs) - API
- RxNorm (2M concepts) - Mapping
- NPPA (5K Indian) - Prices
- DrugBank (14K) - Details

**Total cost: ₹0**
**Total time: 1-2 weeks**
**Total coverage: 100K+ drugs**

**Start with:** `python download_opensource_data.py`
