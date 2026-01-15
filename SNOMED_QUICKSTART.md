# 🚀 SNOMED CT Quick Start

## Setup (One-time)

```bash
# 1. Run automated setup
./scripts/setup_snomed.sh

# 2. Restart API
./stop.sh && ./start.sh

# 3. Test endpoints
./scripts/test_snomed_api.sh
```

## API Examples

### Search Drugs
```bash
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/search?q=metformin"
```

### Get Brand Details
```bash
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/brands/2430421000189104"
```

### Find Alternatives
```bash
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/brands/2430421000189104/alternatives"
```

### Autocomplete
```bash
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/autocomplete?q=met"
```

### Statistics
```bash
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/stats"
```

## What You Get

✅ **89,447 Indian brands** with SNOMED codes  
✅ **9,870 generic formulations**  
✅ **7,935 manufacturers**  
✅ **Fast search** (< 50ms)  
✅ **Alternative finder** (same generic)  
✅ **Autocomplete** support  
✅ **Production-ready** with indexes  

## Documentation

- **Full Guide**: [docs/SNOMED_INTEGRATION.md](docs/SNOMED_INTEGRATION.md)
- **API Docs**: http://localhost:8001/docs
- **Database Schema**: [scripts/setup_snomed_db.sql](scripts/setup_snomed_db.sql)

## Files Created

```
scripts/
├── setup_snomed_db.sql          # Database schema
├── setup_snomed.sh              # Automated setup
├── test_snomed_api.sh           # API tests
└── etl/
    └── load_snomed_data.py      # ETL pipeline

app/
├── api/
│   └── snomed_endpoints.py      # API endpoints (9 endpoints)
└── models/
    └── snomed_models.py         # SQLAlchemy models

docs/
└── SNOMED_INTEGRATION.md        # Complete documentation
```

## Troubleshooting

**Data not loading?**
```bash
# Check logs
tail -f logs/snomed_etl.log

# Verify database
psql -d hms_terminology -c "SELECT COUNT(*) FROM snomed_brands"
```

**Slow queries?**
```sql
-- Refresh materialized view
SELECT refresh_snomed_complete_view();

-- Rebuild indexes
REINDEX TABLE snomed_brands;
```

**API not responding?**
```bash
# Check if service is running
./status.sh

# Restart service
./stop.sh && ./start.sh
```

## Next Steps

1. ✅ Setup complete
2. 🔄 Integrate with frontend
3. 📊 Monitor performance
4. 🔄 Setup auto-updates (weekly cron)

---

**Need help?** Check [docs/SNOMED_INTEGRATION.md](docs/SNOMED_INTEGRATION.md)
