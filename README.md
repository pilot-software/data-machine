# HMS Terminology Service - Enterprise Edition

Enterprise-grade FastAPI microservice for medical terminology (ICD-10, ICD-11) with advanced search, clinical decision support, and performance monitoring.

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/pilot-software/data-machine.git
cd data-machine

# Install dependencies
pip install -r requirements.txt

# Setup database (one-time)
python setup_full_db.py

# Start service
./run.sh
# OR
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

**Service runs on**: `http://localhost:8001`

**API Documentation (Swagger)**: `http://localhost:8001/docs`

**Alternative API Docs (ReDoc)**: `http://localhost:8001/redoc`

## 📊 Database Coverage

- **ICD-10**: 71,704 codes (complete US ICD-10-CM)
- **ICD-11**: 4,239 codes (WHO official API)
- **Total**: 75,943 medical terminology codes

## 🏥 API Endpoints

### Health & Monitoring
```bash
GET /api/v1/health                    # Basic health check
GET /api/v1/health/detailed           # Comprehensive health with metrics
GET /api/v1/health/database           # Database health check
GET /api/v1/health/redis              # Redis health check
```

### Search & Autocomplete
```bash
GET /api/v1/search/unified?query=diabetes&limit=10        # Search both ICD-10 & ICD-11
GET /api/v1/search/icd10?query=diabetes&limit=10          # ICD-10 search
GET /api/v1/autocomplete/icd10?query=diab&limit=10        # ICD-10 autocomplete
GET /api/v1/code/{code}                                    # Get specific code details
```

### Enterprise Features
```bash
GET /api/v1/enterprise/search/icd10/advanced?query=diabetes&limit=10&fuzzy_threshold=0.3
GET /api/v1/enterprise/icd10/{code}/hierarchy              # Get code hierarchy
POST /api/v1/enterprise/clinical/decision-support          # Clinical decision support
GET /api/v1/enterprise/analytics/search-stats              # Search analytics
GET /api/v1/enterprise/chapters                            # ICD-10 chapters list
```

## 🔧 Configuration

### Database Setup
```bash
# PostgreSQL required
createdb hms_terminology

# Update .env file
DATABASE_URL=postgresql://username@localhost:5432/hms_terminology
```

### Environment Variables (.env)
```env
# Database
DATABASE_URL=postgresql://samirkolhe@localhost:5432/hms_terminology

# API Settings
HOST=0.0.0.0
PORT=8001
DEBUG=True

# Performance
CACHE_TTL=3600
MAX_SUGGESTIONS=10
```

## 📈 Sample API Responses

### Unified Search Response
```json
{
  "query": "diabetes",
  "total_results": 3,
  "results": [
    {
      "code": "E0800",
      "title": "Diabetes mellitus due to underlying condition...",
      "chapter": "Diabetes mellitus due to underlying condition with hyperosmolarity",
      "version": "ICD-10",
      "confidence": 0.9,
      "system": "ICD-10-CM"
    }
  ],
  "query_time_ms": 168.51,
  "systems_searched": ["ICD-10-CM"]
}
```

### Autocomplete Response
```json
{
  "suggestions": [
    {
      "code": "E0800",
      "term": "Diabetes mellitus due to underlying condition...",
      "chapter": "Diabetes mellitus due to underlying condition with hyperosmolarity",
      "confidence": 0.8
    }
  ],
  "total_count": 5,
  "query_time_ms": 2.49
}
```

### Advanced Search Response
```json
{
  "results": [...],
  "total_count": 3,
  "query_time_ms": 15.89,
  "search_metadata": {
    "exact_matches": 0,
    "prefix_matches": 3,
    "fuzzy_matches": 0,
    "chapter_filter": null,
    "fuzzy_threshold": 0.3
  }
}
```

## 🏗️ Architecture

### Database Schema
```sql
-- ICD-10 Table (71,704 codes)
icd10_codes (
  id SERIAL PRIMARY KEY,
  code VARCHAR(20) UNIQUE,
  term TEXT,
  short_desc TEXT,
  chapter TEXT,
  category VARCHAR(10),
  search_vector tsvector
)

-- ICD-11 Table (4,239 codes)
icd11_codes (
  id SERIAL PRIMARY KEY,
  code VARCHAR(20) UNIQUE,
  title TEXT,
  definition TEXT,
  chapter TEXT,
  url TEXT,
  search_vector tsvector
)
```

### Performance Features
- **Full-text search** with PostgreSQL tsvector
- **GIN indexes** for sub-10ms queries
- **Batch processing** for large datasets
- **Auto-detection** of ICD versions

## 🔍 Code Format Detection

The system automatically detects ICD versions:

- **ICD-10**: `E11.9`, `I10`, `J18.9` (Letter + digits + decimal)
- **ICD-11**: `5A11`, `6A70`, `BA00` (Digits + Letter + digits)

## 📦 Project Structure

```
data-machine/
├── app/                    # FastAPI application
├── data/                   # Medical terminology datasets
│   ├── icd10_full_processed.csv    # 71,704 ICD-10 codes
│   └── icd11_who_api.json          # 4,239 ICD-11 codes
├── unified_api.py          # Main API server
├── setup_full_db.py        # Database setup script
├── who_icd11_client.py     # WHO API client
├── code_detector.py        # Version detection utility
└── .env                    # Configuration
```

## 🚀 Deployment

### Local Development
```bash
./start.sh
```

### Production
```bash
# Using uvicorn with multiple workers
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 4
```

## 📊 Data Sources

- **ICD-10**: GitHub repository (kamillamagna/ICD-10-CSV)
- **ICD-11**: WHO Official API (icd.who.int)
- **Updates**: Run `python who_icd11_client.py` for fresh ICD-11 data

## 🔧 Maintenance

### Update ICD-11 Data
```bash
python who_icd11_client.py
python setup_full_db.py  # Reload database
```

### Database Backup
```bash
pg_dump hms_terminology > backup.sql
```

### Performance Monitoring
```bash
# Check database size
psql -d hms_terminology -c "SELECT pg_size_pretty(pg_database_size('hms_terminology'));"

# Check table counts
psql -d hms_terminology -c "SELECT 'icd10_codes' as table, count(*) FROM icd10_codes UNION SELECT 'icd11_codes', count(*) FROM icd11_codes;"
```

## 🏥 Enterprise Features

✅ **Real medical data** (75,943 codes)  
✅ **Dual classification support** (ICD-10 + ICD-11)  
✅ **Advanced search algorithms** with confidence scoring  
✅ **Auto-version detection** for seamless queries  
✅ **Full-text search** with PostgreSQL optimization  
✅ **RESTful API** with comprehensive endpoints  
✅ **Production-ready** with proper indexing  
✅ **Scalable architecture** for enterprise deployment

## 📞 Support

For issues or questions:
1. Check API health: `GET /api/v1/health`
2. Verify database: `psql -d hms_terminology -c "\dt"`
3. Review logs: `tail -f logs/app.log`

---

**HMS Terminology Service** - Enterprise medical terminology at your fingertips! 🏥