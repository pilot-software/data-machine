# 🚀 New Engineer Onboarding Guide

## 📋 Quick Start (5 Minutes)

```bash
# 1. Clone & Setup
git clone <repo-url>
cd data-machine
./import_database.sh database_dumps/hms_database_20260115_112015.tar.gz
./start.sh

# 2. Test API
curl http://localhost:8001/api/v1/health
curl -H "X-API-Key: dev-key-123" "http://localhost:8001/api/v1/snomed/search?q=paracetamol"

# 3. Explore
open http://localhost:8001/docs
```

**You're ready to code!** 🎉

---

## 📁 Project Structure (What Matters)

```
data-machine/
├── app/                          # Main application code
│   ├── api/                      # API endpoints (START HERE)
│   │   ├── snomed_endpoints.py   # Drug search (89K brands)
│   │   ├── icd_endpoints.py      # ICD-10 codes
│   │   └── clinical_ai_endpoints.py  # AI diagnosis
│   ├── core/                     # Configuration & setup
│   │   ├── settings.py           # Environment variables
│   │   └── dependencies.py       # Dependency injection
│   ├── db/                       # Database layer
│   │   ├── models.py             # SQLAlchemy models
│   │   └── database.py           # DB connection
│   ├── services/                 # Business logic
│   │   ├── cache_service.py      # Redis caching
│   │   └── terminology_service.py # Core logic
│   └── main.py                   # FastAPI app entry point
│
├── scripts/                      # Utility scripts
│   └── etl/                      # Data loading scripts
│
├── tests/                        # Test files
│
├── .env                          # Environment config (create from .env.example)
├── requirements.txt              # Python dependencies
│
# Daily use scripts
├── start.sh                      # Start server
├── stop.sh                       # Stop server
├── status.sh                     # Check status
└── test_all.sh                   # Run tests
```

---

## 🎯 Core Concepts

### 1. What This API Does
- **Drug Search**: 89,446 Indian drug brands with SNOMED codes
- **ICD Codes**: 71,704 diagnosis codes for insurance
- **AI Diagnosis**: Grok/Ollama powered clinical assistant
- **Drug Classification**: Antibiotics, analgesics, etc.

### 2. Key Technologies
- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Database (89K+ drugs, ICD codes)
- **Redis**: Caching (optional)
- **SQLAlchemy**: ORM for database
- **Pydantic**: Data validation

### 3. Authentication
All endpoints (except `/health`) require:
```bash
X-API-Key: dev-key-123
```

---

## 🔍 Code Flow Example

### Example: Drug Search Request

```
User Request: GET /api/v1/snomed/search?q=paracetamol
    ↓
app/main.py (FastAPI app)
    ↓
app/middleware/auth.py (API key check)
    ↓
app/api/snomed_endpoints.py (endpoint handler)
    ↓
app/services/terminology_service.py (business logic)
    ↓
app/db/models.py (database query)
    ↓
PostgreSQL Database
    ↓
Response: 4,426 paracetamol brands
```

---

## 📖 Essential Files to Read First

### Day 1: Understanding the API
1. **README.md** - Project overview
2. **app/main.py** - Application entry point
3. **app/api/snomed_endpoints.py** - Drug search endpoints
4. **app/api/icd_endpoints.py** - ICD code endpoints

### Day 2: Understanding the Data
5. **app/db/models.py** - Database schema
6. **app/services/terminology_service.py** - Core business logic
7. **API.md** - API documentation with examples

### Day 3: Advanced Features
8. **app/api/clinical_ai_endpoints.py** - AI diagnosis
9. **app/middleware/auth.py** - Authentication
10. **app/services/cache_service.py** - Caching

---

## 🛠️ Common Development Tasks

### Add a New Endpoint

```python
# app/api/my_endpoints.py
from fastapi import APIRouter, Depends
from app.middleware.auth import verify_api_key

router = APIRouter(
    prefix="/api/v1/my-feature",
    tags=["my-feature"],
    dependencies=[Depends(verify_api_key)]
)

@router.get("/search")
async def search_something(q: str):
    return {"query": q, "results": []}
```

```python
# app/main.py
from app.api.my_endpoints import router as my_router
app.include_router(my_router)
```

### Add a Database Model

```python
# app/db/models.py
class MyModel(Base):
    __tablename__ = "my_table"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
```

### Add a Service

```python
# app/services/my_service.py
class MyService:
    def __init__(self, db):
        self.db = db
    
    def do_something(self):
        return self.db.query(MyModel).all()
```

---

## 🧪 Testing

```bash
# Run all tests
./test_all.sh

# Run specific test
python -m pytest tests/test_api_consolidated.py -v

# Test single endpoint
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/search?q=test"
```

---

## 🐛 Debugging

### Check Logs
```bash
tail -f logs/server.log      # Application logs
tail -f logs/error.log       # Error logs
```

### Check Database
```bash
psql -U your_user -d medical_library
\dt                          # List tables
SELECT COUNT(*) FROM snomed_brands;  # Check data
```

### Common Issues

**Issue**: Server won't start
```bash
./stop.sh                    # Kill existing process
./start.sh                   # Restart
```

**Issue**: Database connection error
```bash
# Check .env file
cat .env

# Test database connection
psql -U your_user -d medical_library -c "SELECT 1;"
```

**Issue**: Missing data
```bash
# Re-import database
./import_database.sh database_dumps/hms_database_20260115_112015.tar.gz
```

---

## 📚 API Examples

### 1. Search Drugs
```bash
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/search?q=paracetamol&page=1&page_size=10"
```

### 2. Get Drug Details
```bash
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/brands/2430421000189104"
```

### 3. Find Alternatives
```bash
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/brands/2430421000189104/alternatives"
```

### 4. Search ICD Codes
```bash
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/icd/search?q=diabetes"
```

### 5. AI Diagnosis
```bash
curl -X POST -H "X-API-Key: dev-key-123" \
  -H "Content-Type: application/json" \
  -d '{"symptoms":["fever","cough"],"patient_age":35}' \
  "http://localhost:8001/api/v1/clinical-ai/diagnose"
```

---

## 🎓 Learning Path

### Week 1: Basics
- [ ] Setup development environment
- [ ] Understand project structure
- [ ] Read core API endpoints
- [ ] Make first API call
- [ ] Run tests successfully

### Week 2: Features
- [ ] Add a simple endpoint
- [ ] Understand database models
- [ ] Learn caching mechanism
- [ ] Understand authentication

### Week 3: Advanced
- [ ] Work on AI diagnosis feature
- [ ] Optimize database queries
- [ ] Add new service
- [ ] Write tests

### Week 4: Production
- [ ] Deploy to staging
- [ ] Monitor logs
- [ ] Handle errors
- [ ] Performance optimization

---

## 💡 Best Practices

### Code Style
```python
# ✅ Good: Clear, documented
@router.get("/search")
async def search_drugs(
    q: str = Query(..., min_length=2, description="Search query")
):
    """Search drugs by name or generic."""
    return await drug_service.search(q)

# ❌ Bad: No docs, unclear
@router.get("/s")
async def s(q: str):
    return db.query(Drug).filter(Drug.name.like(f"%{q}%")).all()
```

### Error Handling
```python
# ✅ Good: Proper error handling
try:
    result = await drug_service.search(query)
    return result
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    raise HTTPException(503, "Service unavailable")

# ❌ Bad: No error handling
result = await drug_service.search(query)
return result
```

### Database Queries
```python
# ✅ Good: Parameterized query
db.execute(text("SELECT * FROM drugs WHERE name = :name"), {"name": name})

# ❌ Bad: SQL injection risk
db.execute(f"SELECT * FROM drugs WHERE name = '{name}'")
```

---

## 🔗 Useful Links

- **API Docs**: http://localhost:8001/docs
- **Database Schema**: See `app/db/models.py`
- **Environment Config**: `.env` file
- **Logs**: `logs/` directory

---

## 🆘 Getting Help

1. **Check logs**: `tail -f logs/server.log`
2. **Read docs**: `docs/` folder
3. **Test endpoint**: Use Swagger UI at `/docs`
4. **Ask team**: Create GitHub issue

---

## ✅ Checklist for New Engineers

- [ ] Repository cloned
- [ ] Database imported
- [ ] Server running on port 8001
- [ ] API key working (dev-key-123)
- [ ] Can search drugs via API
- [ ] Can search ICD codes
- [ ] Tests passing
- [ ] Read core files (main.py, snomed_endpoints.py)
- [ ] Made first code change
- [ ] Understand deployment process

**Welcome to the team! 🎉**
