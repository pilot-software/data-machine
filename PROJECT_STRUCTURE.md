# 📁 Project Structure Guide

## 🎯 Quick Navigation

```
data-machine/
│
├── 🚀 START HERE
│   ├── README.md                    # Project overview
│   ├── ONBOARDING_GUIDE.md         # New engineer guide
│   └── API.md                       # API documentation
│
├── 💻 DAILY USE SCRIPTS
│   ├── start.sh                     # Start server
│   ├── stop.sh                      # Stop server
│   ├── status.sh                    # Check status
│   ├── restart.sh                   # Restart server
│   ├── test_all.sh                  # Run tests
│   ├── import_database.sh           # Import database
│   ├── export_database.sh           # Export database
│   └── cleanup.sh                   # Remove redundant files
│
├── 📝 MAIN CODE (app/)
│   ├── main.py                      # FastAPI app entry point
│   │
│   ├── api/                         # API Endpoints (9 files)
│   │   ├── snomed_endpoints.py      # ⭐ Drug search (89K brands)
│   │   ├── icd_endpoints.py         # ⭐ ICD-10 codes
│   │   ├── clinical_ai_endpoints.py # ⭐ AI diagnosis
│   │   ├── snomed_extended_endpoints.py
│   │   ├── health_endpoints.py
│   │   ├── abhbp_endpoints.py
│   │   ├── clinical_endpoints.py
│   │   ├── admin_endpoints.py
│   │   └── analytics_endpoints.py
│   │
│   ├── core/                        # Configuration (7 files)
│   │   ├── settings.py              # ⭐ Environment variables
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   ├── exceptions.py
│   │   ├── logging_config.py
│   │   ├── service_factory.py
│   │   └── circuit_breaker.py
│   │
│   ├── db/                          # Database (4 files)
│   │   ├── models.py                # ⭐ Database schema
│   │   ├── database.py              # ⭐ DB connection
│   │   ├── indexing.py
│   │   └── partitioning.py
│   │
│   ├── services/                    # Business Logic (10 files)
│   │   ├── terminology_service.py   # ⭐ Core logic
│   │   ├── cache_service.py         # Redis caching
│   │   ├── icd10_service.py
│   │   ├── health_service.py
│   │   ├── enterprise_search.py
│   │   ├── performance_monitor.py
│   │   ├── redis_cluster.py
│   │   ├── redis_service.py
│   │   ├── rxnav_service.py
│   │   ├── safety_rules.py
│   │   └── search_logger.py
│   │
│   ├── middleware/                  # Middleware (3 files)
│   │   ├── auth.py                  # ⭐ API key authentication
│   │   ├── rate_limiter.py
│   │   └── audit_logger.py
│   │
│   ├── models/                      # Data Models (3 files)
│   │   ├── snomed_models.py
│   │   ├── terminology.py
│   │   └── validation.py
│   │
│   ├── repositories/                # Data Access (4 files)
│   │   ├── base_repository.py
│   │   ├── icd10_repository.py
│   │   ├── async_icd10_repository.py
│   │   └── health_repository.py
│   │
│   └── utils/                       # Utilities (1 file)
│       └── sanitizer.py
│
├── 🧪 TESTS (tests/)
│   ├── test_api_consolidated.py     # ⭐ Main API tests
│   ├── test_abhbp_api.py
│   └── test_architecture.py
│
├── 🔧 SCRIPTS (scripts/)
│   ├── etl/                         # Data Loading (5 files)
│   │   ├── load_snomed_data.py      # Load SNOMED drugs
│   │   ├── load_snomed_rf2_extended.py
│   │   ├── download_icd10_complete.py
│   │   ├── load_abhbp_data.py
│   │   └── download_abhbp_data.py
│   │
│   └── cron/                        # Scheduled Tasks (3 files)
│       ├── cron_update_drugs.sh
│       ├── scheduler_airflow.py
│       └── setup_cron.sh
│
├── 📚 DOCS (docs/)
│   ├── SNOMED_INTEGRATION.md        # SNOMED technical reference
│   ├── SNOMED_MIGRATION_GUIDE.md    # Migration guide
│   ├── ABHBP_INTEGRATION.md         # ABHBP integration
│   └── AUTH_GUIDE.md                # Security reference
│
├── 📖 MORE DOCS (root)
│   ├── DEPLOYMENT.md                # Deployment guide
│   ├── WORKFLOW.md                  # Usage patterns
│   ├── LLM_SETUP_GUIDE.md          # AI configuration
│   └── CODE_QUALITY_ANALYSIS.md    # Code quality report
│
├── 💾 DATABASE
│   └── database_dumps/              # Database backups
│       └── hms_database_*.tar.gz
│
└── ⚙️ CONFIG
    ├── .env                         # ⭐ Environment variables
    ├── .env.example                 # Environment template
    ├── requirements.txt             # ⭐ Python dependencies
    └── .gitignore                   # Git ignore rules
```

---

## 🎯 Where to Start?

### Day 1: Setup & Explore
1. Read `README.md` (5 min)
2. Read `ONBOARDING_GUIDE.md` (10 min)
3. Run `./import_database.sh` and `./start.sh` (5 min)
4. Test API at http://localhost:8001/docs (10 min)

### Day 2: Understand Code
5. Read `app/main.py` - Application entry point
6. Read `app/api/snomed_endpoints.py` - Drug search API
7. Read `app/db/models.py` - Database schema
8. Read `API.md` - API examples

### Day 3: Make Changes
9. Add a simple endpoint in `app/api/`
10. Test with `./test_all.sh`
11. Read `DEPLOYMENT.md` for production

---

## 📊 File Count Summary

| Category | Files | Purpose |
|----------|-------|---------|
| **Core App** | 41 | Main application code |
| **Tests** | 3 | Test files |
| **Scripts** | 8 | ETL and cron jobs |
| **Docs** | 10 | Documentation |
| **Root Scripts** | 8 | Daily use commands |
| **Config** | 3 | Environment & dependencies |
| **Total** | 73 | Essential files only |

---

## 🔍 Key Files Explained

### Must Read (Top 10)
1. **README.md** - Start here
2. **ONBOARDING_GUIDE.md** - New engineer guide
3. **app/main.py** - FastAPI app
4. **app/api/snomed_endpoints.py** - Drug search
5. **app/api/icd_endpoints.py** - ICD codes
6. **app/db/models.py** - Database schema
7. **app/core/settings.py** - Configuration
8. **app/middleware/auth.py** - Authentication
9. **API.md** - API documentation
10. **DEPLOYMENT.md** - Deployment guide

### Important (Next 10)
11. **app/services/terminology_service.py** - Business logic
12. **app/db/database.py** - Database connection
13. **app/api/clinical_ai_endpoints.py** - AI features
14. **app/services/cache_service.py** - Caching
15. **tests/test_api_consolidated.py** - Tests
16. **scripts/etl/load_snomed_data.py** - Data loading
17. **app/middleware/rate_limiter.py** - Rate limiting
18. **app/core/exceptions.py** - Error handling
19. **WORKFLOW.md** - Usage patterns
20. **LLM_SETUP_GUIDE.md** - AI setup

---

## 🚀 Quick Commands

```bash
# Setup
./import_database.sh database_dumps/hms_database_*.tar.gz

# Daily use
./start.sh                    # Start server
./stop.sh                     # Stop server
./status.sh                   # Check status
./test_all.sh                 # Run tests

# Cleanup
./cleanup.sh                  # Remove redundant files

# Development
tail -f logs/server.log       # View logs
curl http://localhost:8001/docs  # API docs
```

---

## 💡 Tips for Navigation

1. **Use your IDE's file search** (Cmd+P / Ctrl+P)
2. **Search for text** (Cmd+Shift+F / Ctrl+Shift+F)
3. **Follow imports** to understand dependencies
4. **Start with endpoints** in `app/api/`
5. **Check models** in `app/db/models.py` for database schema

---

## 🎓 Learning Path

```
Week 1: Basics
├── Setup environment
├── Understand project structure
├── Read core files
└── Make first API call

Week 2: Features
├── Add simple endpoint
├── Understand database
├── Learn caching
└── Understand auth

Week 3: Advanced
├── Work on AI features
├── Optimize queries
├── Add new service
└── Write tests

Week 4: Production
├── Deploy to staging
├── Monitor logs
├── Handle errors
└── Performance tuning
```

---

## 📞 Need Help?

1. Check `ONBOARDING_GUIDE.md`
2. Read `API.md` for examples
3. Check logs: `tail -f logs/server.log`
4. Test endpoint: http://localhost:8001/docs
5. Ask team: Create GitHub issue

---

**Happy Coding! 🚀**
