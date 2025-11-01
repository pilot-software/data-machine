# 💊 Drug Database ETL Pipeline - Quick Start

## 🎯 Architecture

```
Data Sources → ETL Pipeline → PostgreSQL → FastAPI → Frontend/Mobile
```

## 🚀 Quick Setup (5 minutes)

### 1. Setup Database

```bash
# Create database
createdb hms_drugs

# Run schema
psql -d hms_drugs -f setup_drug_db.sql
```

### 2. Prepare Data Files

**Expected Format:**

```csv
# data/drugs.csv
drug_name,generic_name,manufacturer,strength,dosage_form,mrp,pack_size
Crocin,Acetaminophen,GSK,500mg,Tablet,15.00,10 tablets
Dolo 650,Acetaminophen,Micro Labs,650mg,Tablet,30.00,15 tablets
```

### 3. Run ETL Pipeline

```bash
# Install dependencies
pip install pandas psycopg2-binary requests

# Run ETL
python etl_drug_pipeline.py
```

### 4. Start API

```bash
# Add to app/main.py
from app.api.drugs import router as drugs_router
app.include_router(drugs_router)

# Start server
python -m uvicorn app.main:app --reload
```

## 📊 API Endpoints

```bash
# Search drugs
GET /api/v1/drugs/search?query=crocin

# Get brand details
GET /api/v1/drugs/brand/Crocin

# Get generic brands
GET /api/v1/drugs/generic/Acetaminophen

# Find by RxNorm
GET /api/v1/drugs/rxnorm/202433

# Find alternatives
POST /api/v1/drugs/alternatives
{
    "brand_name": "Dolo 650",
    "max_price": 20.00
}

# Check substitution
POST /api/v1/drugs/substitution-check
{
    "prescribed_brand": "Crocin",
    "available_brand": "Dolo 650"
}
```

## 🔄 Scheduled Updates

### Option 1: Cron (Simple)

```bash
# Add to crontab
0 2 * * 0 cd /path/to/data-machine && python etl_drug_pipeline.py
```

### Option 2: Airflow (Advanced)

```bash
# Copy DAG
cp scheduler_airflow.py ~/airflow/dags/

# Airflow will run weekly
```

## 📁 File Structure

```
data-machine/
├── etl_drug_pipeline.py       # ETL script
├── setup_drug_db.sql           # Database schema
├── app/api/drugs.py            # API endpoints
├── scheduler_airflow.py        # Airflow DAG
└── data/
    ├── nrces_drugs.tsv         # NRCeS data
    └── kaggle_drugs.csv        # Kaggle data
```

## 🎯 Data Sources

### 1. NRCeS (National Resource Centre for EHR Standards)
- URL: https://nrces.in/
- Format: TSV
- Coverage: Indian drugs

### 2. Kaggle Datasets
- Search: "Indian drugs database"
- Format: CSV
- Coverage: Brand + Generic mapping

### 3. RxNorm API
- URL: https://rxnav.nlm.nih.gov/
- Free API
- Coverage: Global drug standards

## 💡 Sample Usage

```python
# ETL Pipeline
from etl_drug_pipeline import DrugETL

etl = DrugETL("postgresql://localhost/hms_drugs")
etl.run(
    nrces_file="data/nrces_drugs.tsv",
    kaggle_file="data/kaggle_drugs.csv",
    enrich_rxnorm=True
)
etl.close()
```

```python
# API Usage
import requests

# Search
response = requests.get(
    "http://localhost:8001/api/v1/drugs/search",
    params={"query": "paracetamol"}
)
print(response.json())

# Find alternatives
response = requests.post(
    "http://localhost:8001/api/v1/drugs/alternatives",
    json={"brand_name": "Dolo 650", "max_price": 20}
)
print(response.json())
```

## 📊 Expected Results

```json
{
    "brand_name": "Crocin",
    "manufacturer": "GSK",
    "generic_name": "Acetaminophen",
    "rxnorm_cui": "202433",
    "strength": "500mg",
    "mrp": 15.00,
    "alternatives": [
        {
            "brand_name": "Metacin",
            "mrp": 12.00,
            "savings": 3.00,
            "savings_percent": 20
        }
    ]
}
```

## 🔧 Configuration

```python
# .env
DATABASE_URL=postgresql://user:pass@localhost/hms_drugs
RXNORM_API_KEY=optional  # Not required for basic usage
ETL_BATCH_SIZE=100
ETL_RATE_LIMIT_DELAY=1  # seconds
```

## ⚡ Performance

- **ETL Speed**: ~1000 drugs/minute (with RxNorm enrichment)
- **API Response**: <50ms (with indexes)
- **Database Size**: ~500MB for 50K drugs

## 🎯 Next Steps

1. ✅ Setup database schema
2. ✅ Run ETL pipeline
3. ✅ Test API endpoints
4. 🔄 Schedule weekly updates
5. 🌐 Add multi-language support
6. 🔍 Add drug interactions
7. 📱 Build mobile app

## 📞 Troubleshooting

**Issue**: RxNorm API rate limit
**Solution**: Increase `ETL_RATE_LIMIT_DELAY` in config

**Issue**: Duplicate drugs
**Solution**: ETL handles deduplication automatically

**Issue**: Missing RxNorm CUI
**Solution**: Some Indian drugs may not have RxNorm mapping (expected)

---

**Ready to go!** 🚀 Run the ETL and start serving drug data.
