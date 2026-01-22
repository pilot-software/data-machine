# 🔄 Migration Guide: Legacy Drugs → SNOMED CT

## Overview

Migrate from legacy drug database (114 brands) to SNOMED CT (89,447 brands) without breaking existing functionality.

---

## 📊 Comparison

| Feature | Legacy | SNOMED CT |
|---------|--------|-----------|
| Brands | 114 | 89,447 |
| Standard codes | RxNorm only | SNOMED + RxNorm |
| Manufacturers | Limited | 7,935 |
| Alternatives | Manual | Automatic |
| Search | Basic | Full-text + relevance |
| Updates | Manual | Automated |

---

## 🎯 Migration Strategy

### Phase 1: Parallel Run (Week 1)
- ✅ Keep legacy endpoints active
- ✅ Add SNOMED endpoints
- ✅ Test both systems
- ✅ Compare results

### Phase 2: Gradual Migration (Week 2-3)
- ✅ Update frontend to use SNOMED
- ✅ Maintain backward compatibility
- ✅ Monitor performance
- ✅ Fix issues

### Phase 3: Deprecation (Week 4)
- ✅ Mark legacy endpoints as deprecated
- ✅ Add deprecation warnings
- ✅ Update documentation
- ✅ Notify users

### Phase 4: Removal (Month 2)
- ✅ Remove legacy endpoints
- ✅ Clean up database
- ✅ Update tests
- ✅ Final documentation

---

## 🔧 Implementation Steps

### Step 1: Setup SNOMED Database

```bash
# Run setup script
./scripts/setup_snomed.sh

# Verify data
psql -d medical_library -c "SELECT COUNT(*) FROM snomed_brands"
```

### Step 2: Update API Routes

**Before (Legacy):**
```python
# app/api/drug_endpoints.py
@router.get("/drugs/search")
async def search_drugs(q: str):
    # Search 114 brands
    return legacy_search(q)
```

**After (Both):**
```python
# Keep legacy endpoint
@router.get("/drugs/search")
async def search_drugs_legacy(q: str):
    # Add deprecation warning
    warnings.warn("Use /snomed/search instead", DeprecationWarning)
    return legacy_search(q)

# New SNOMED endpoint
@router.get("/snomed/search")
async def search_snomed_drugs(q: str):
    # Search 89K brands
    return snomed_search(q)
```

### Step 3: Update Frontend

**Before:**
```javascript
// Old API call
const results = await fetch('/api/v1/drugs/search?q=metformin');
```

**After:**
```javascript
// New API call with fallback
async function searchDrugs(query) {
  try {
    // Try SNOMED first
    const results = await fetch(`/api/v1/snomed/search?q=${query}`);
    return results;
  } catch (error) {
    // Fallback to legacy
    console.warn('SNOMED unavailable, using legacy');
    return await fetch(`/api/v1/drugs/search?q=${query}`);
  }
}
```

### Step 4: Data Mapping

**Map legacy IDs to SNOMED IDs:**

```sql
-- Create mapping table
CREATE TABLE drug_id_mapping (
    legacy_id INTEGER,
    snomed_id BIGINT,
    brand_name TEXT,
    mapped_at TIMESTAMP DEFAULT NOW()
);

-- Map by brand name
INSERT INTO drug_id_mapping (legacy_id, snomed_id, brand_name)
SELECT 
    l.brand_id as legacy_id,
    s.snomed_id,
    l.brand_name
FROM indian_brand_drugs l
JOIN snomed_brands s ON LOWER(l.brand_name) = LOWER(s.brand_name)
WHERE l.active = TRUE;

-- Check mapping coverage
SELECT 
    COUNT(*) as total_legacy,
    COUNT(m.snomed_id) as mapped,
    COUNT(*) - COUNT(m.snomed_id) as unmapped
FROM indian_brand_drugs l
LEFT JOIN drug_id_mapping m ON l.brand_id = m.legacy_id;
```

### Step 5: Update Database Queries

**Before:**
```python
# Legacy query
drug = db.query(IndianBrandDrug).filter_by(brand_id=123).first()
```

**After:**
```python
# Try SNOMED first, fallback to legacy
def get_drug(drug_id: int, is_snomed: bool = True):
    if is_snomed:
        return db.query(SnomedBrand).filter_by(snomed_id=drug_id).first()
    else:
        # Legacy fallback
        return db.query(IndianBrandDrug).filter_by(brand_id=drug_id).first()
```

### Step 6: Update Stored Data

**Migrate existing prescriptions:**

```sql
-- Add SNOMED ID column to prescriptions
ALTER TABLE prescriptions ADD COLUMN drug_snomed_id BIGINT;

-- Map existing prescriptions
UPDATE prescriptions p
SET drug_snomed_id = m.snomed_id
FROM drug_id_mapping m
WHERE p.drug_id = m.legacy_id;

-- Check migration status
SELECT 
    COUNT(*) as total_prescriptions,
    COUNT(drug_snomed_id) as migrated,
    COUNT(*) - COUNT(drug_snomed_id) as pending
FROM prescriptions;
```

---

## 🔍 Testing Checklist

### Functional Tests
- [ ] Search returns results from SNOMED
- [ ] Brand details load correctly
- [ ] Alternatives finder works
- [ ] Autocomplete responds fast
- [ ] Legacy endpoints still work
- [ ] Data mapping is accurate

### Performance Tests
- [ ] Search < 50ms
- [ ] Autocomplete < 20ms
- [ ] No memory leaks
- [ ] Database connections stable

### Integration Tests
- [ ] Frontend displays SNOMED data
- [ ] Prescriptions save with SNOMED IDs
- [ ] Reports use correct data
- [ ] Analytics updated

### Backward Compatibility
- [ ] Old API calls still work
- [ ] Existing data accessible
- [ ] No breaking changes
- [ ] Deprecation warnings shown

---

## 🚨 Rollback Plan

If issues occur, rollback is simple:

```bash
# 1. Stop using SNOMED endpoints
# Update frontend to use legacy endpoints

# 2. Keep SNOMED data (don't delete)
# Can retry migration later

# 3. Monitor legacy system
tail -f logs/app.log | grep "drugs/search"

# 4. Fix issues and retry
# SNOMED data remains intact
```

---

## 📊 Monitoring

### Metrics to Track

```sql
-- API usage comparison
SELECT 
    endpoint,
    COUNT(*) as requests,
    AVG(response_time_ms) as avg_response_time
FROM api_logs
WHERE endpoint IN ('/drugs/search', '/snomed/search')
AND created_at > NOW() - INTERVAL '7 days'
GROUP BY endpoint;

-- Data quality
SELECT 
    'Legacy' as source,
    COUNT(*) as total,
    COUNT(CASE WHEN active THEN 1 END) as active
FROM indian_brand_drugs
UNION ALL
SELECT 
    'SNOMED' as source,
    COUNT(*) as total,
    COUNT(CASE WHEN active THEN 1 END) as active
FROM snomed_brands;

-- Migration progress
SELECT 
    COUNT(*) as total_records,
    COUNT(drug_snomed_id) as migrated,
    ROUND(COUNT(drug_snomed_id)::NUMERIC / COUNT(*) * 100, 2) as percent_complete
FROM prescriptions;
```

---

## 🎯 Success Criteria

### Week 1
- [x] SNOMED database setup complete
- [x] API endpoints deployed
- [x] Tests passing
- [ ] Frontend integration started

### Week 2
- [ ] 50% of traffic on SNOMED
- [ ] Performance metrics met
- [ ] No critical bugs
- [ ] User feedback positive

### Week 3
- [ ] 90% of traffic on SNOMED
- [ ] Legacy endpoints deprecated
- [ ] Documentation updated
- [ ] Training completed

### Week 4
- [ ] 100% migration complete
- [ ] Legacy endpoints removed
- [ ] Monitoring stable
- [ ] Rollback plan tested

---

## 💡 Best Practices

### 1. Feature Flags
```python
# Use feature flags for gradual rollout
ENABLE_SNOMED = os.getenv('ENABLE_SNOMED', 'false').lower() == 'true'

@router.get("/drugs/search")
async def search_drugs(q: str):
    if ENABLE_SNOMED:
        return await search_snomed_drugs(q)
    else:
        return await search_legacy_drugs(q)
```

### 2. A/B Testing
```python
# Route 50% of users to SNOMED
import random

def get_search_endpoint(user_id: int):
    if random.random() < 0.5:
        return "snomed"
    else:
        return "legacy"
```

### 3. Logging
```python
# Log which endpoint is used
logger.info(f"Drug search: endpoint={endpoint}, query={q}, user={user_id}")
```

### 4. Graceful Degradation
```python
# Always have fallback
try:
    return await snomed_search(q)
except Exception as e:
    logger.error(f"SNOMED search failed: {e}")
    return await legacy_search(q)
```

---

## 🔧 Troubleshooting

### Issue: SNOMED search returns no results

**Solution:**
```sql
-- Check if data loaded
SELECT COUNT(*) FROM snomed_brands;

-- Refresh materialized view
SELECT refresh_snomed_complete_view();

-- Rebuild indexes
REINDEX TABLE snomed_brands;
```

### Issue: Slow performance

**Solution:**
```sql
-- Analyze query plan
EXPLAIN ANALYZE 
SELECT * FROM snomed_drugs_complete 
WHERE brand_name ILIKE '%metformin%';

-- Update statistics
ANALYZE snomed_brands;
ANALYZE snomed_generics;
```

### Issue: Mapping incomplete

**Solution:**
```sql
-- Find unmapped drugs
SELECT l.brand_name, l.brand_id
FROM indian_brand_drugs l
LEFT JOIN drug_id_mapping m ON l.brand_id = m.legacy_id
WHERE m.snomed_id IS NULL
AND l.active = TRUE;

-- Manual mapping
INSERT INTO drug_id_mapping (legacy_id, snomed_id, brand_name)
VALUES (123, 2430421000189104, 'Crocin 500mg');
```

---

## 📞 Support

### During Migration
- Monitor: `tail -f logs/app.log`
- Check errors: `grep ERROR logs/app.log`
- Database: `psql -d medical_library`

### After Migration
- Performance: `GET /api/v1/snomed/stats`
- Health: `GET /api/v1/health`
- Metrics: Check monitoring dashboard

---

## ✅ Final Checklist

- [ ] SNOMED database setup complete
- [ ] API endpoints tested
- [ ] Frontend updated
- [ ] Data mapping verified
- [ ] Performance benchmarks met
- [ ] Backward compatibility maintained
- [ ] Rollback plan ready
- [ ] Monitoring configured
- [ ] Documentation updated
- [ ] Team trained
- [ ] Users notified
- [ ] Legacy deprecation scheduled

---

**Migration Timeline: 4 weeks**  
**Risk Level: Low (parallel run + rollback)**  
**Expected Downtime: 0 minutes**  

🚀 **Ready to migrate!**
