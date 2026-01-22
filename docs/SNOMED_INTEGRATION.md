# 🏥 SNOMED CT Indian Drug Database Integration

## 📊 Overview

Successfully integrated **89,447 Indian drug brands** with SNOMED CT codes into the HMS Terminology Service.

### What's Included

| Component | Count | Description |
|-----------|-------|-------------|
| **Brands** | 89,447 | Indian brand names with SNOMED codes |
| **Generics** | 9,870 | Generic formulations |
| **Products** | 68,517 | Product names |
| **Suppliers** | 7,935 | Manufacturers/suppliers |
| **Substances** | 28,913 | Active pharmaceutical ingredients |
| **Drug Forms** | 423 | Dosage forms (tablet, capsule, etc.) |
| **Routes** | 161 | Routes of administration |

## 🚀 Quick Start

### 1. Setup Database

```bash
# Run automated setup (5-10 minutes)
./scripts/setup_snomed.sh
```

This will:
- ✅ Create database schema with indexes
- ✅ Load all 7 data files (205K+ records)
- ✅ Create materialized views for performance
- ✅ Verify data integrity
- ✅ Optimize indexes

### 2. Restart API Service

```bash
./stop.sh
./start.sh
```

### 3. Test Endpoints

```bash
# Get statistics
curl -H "X-API-Key: dev-key-123" \
  http://localhost:8001/api/v1/snomed/stats

# Search drugs
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/search?q=metformin"

# Autocomplete
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/autocomplete?q=cro"
```

## 📡 API Endpoints

### 1. Search Drugs

```bash
GET /api/v1/snomed/search?q=<query>&page=1&page_size=20
```

**Search by:**
- Brand name (e.g., "Crocin")
- Generic name (e.g., "Paracetamol")
- Indication (e.g., "fever")
- Manufacturer (e.g., "GSK")

**Response:**
```json
{
  "query": "metformin",
  "total": 523,
  "page": 1,
  "page_size": 20,
  "response_time_ms": 45.2,
  "results": [
    {
      "snomed_id": 2430421000189104,
      "brand_name": "Glycomet 500mg Tablet",
      "generic_name": "Metformin",
      "generic_snomed_id": 1321000189104,
      "supplier_name": "USV Ltd",
      "manufacturer_country": "India",
      "license_status": "APPROVED",
      "indication": "Type 2 Diabetes",
      "therapeutic_role": "Antidiabetic",
      "active": true
    }
  ]
}
```

### 2. Get Brand Details

```bash
GET /api/v1/snomed/brands/{snomed_id}
```

Returns complete information for a specific brand including generic, manufacturer, and indications.

### 3. Find Alternatives

```bash
GET /api/v1/snomed/brands/{snomed_id}/alternatives?limit=20
```

**Use Case:** Find cheaper alternatives with same generic formulation

**Response:**
```json
[
  {
    "snomed_id": 2430431000189102,
    "brand_name": "Glyciphage 500mg",
    "supplier_name": "Lupin Ltd",
    "license_status": "APPROVED",
    "same_generic": true
  }
]
```

### 4. Get Generic Details

```bash
GET /api/v1/snomed/generics/{snomed_id}
```

Returns generic formulation with brand count, indications, and contraindications.

### 5. Get Brands by Generic

```bash
GET /api/v1/snomed/generics/{snomed_id}/brands?page=1&page_size=20
```

List all brands containing a specific generic formulation.

### 6. Get Supplier Details

```bash
GET /api/v1/snomed/suppliers/{snomed_id}
```

Returns manufacturer information with drug count.

### 7. Get Drugs by Supplier

```bash
GET /api/v1/snomed/suppliers/{snomed_id}/drugs?page=1&page_size=20
```

List all drugs manufactured by a specific supplier.

### 8. Autocomplete

```bash
GET /api/v1/snomed/autocomplete?q=<prefix>&limit=10
```

Fast typeahead suggestions for brand and generic names.

### 9. Statistics

```bash
GET /api/v1/snomed/stats
```

Returns database statistics and coverage information.

## 🎯 Use Cases

### 1. Doctor Prescribing

```javascript
// Search for drug
const results = await fetch('/api/v1/snomed/search?q=metformin');

// Doctor selects brand
const brand = results[0];

// Store SNOMED code in prescription
prescription.drug_snomed_id = brand.snomed_id;
```

### 2. Pharmacy Substitution

```javascript
// Get prescribed drug
const prescribed = await fetch(`/api/v1/snomed/brands/${snomed_id}`);

// Find cheaper alternatives
const alternatives = await fetch(
  `/api/v1/snomed/brands/${snomed_id}/alternatives`
);

// Show alternatives to pharmacist
alternatives.forEach(alt => {
  console.log(`${alt.brand_name} - ${alt.supplier_name}`);
});
```

### 3. Insurance Claims

```javascript
// Validate drug against approved list
const drug = await fetch(`/api/v1/snomed/brands/${snomed_id}`);

if (drug.license_status === 'APPROVED') {
  // Process claim
  processClaim(drug);
}
```

### 4. Drug Inventory

```javascript
// Get all drugs by manufacturer
const drugs = await fetch(
  `/api/v1/snomed/suppliers/${supplier_id}/drugs`
);

// Update inventory
updateInventory(drugs);
```

## 🏗️ Database Architecture

### Tables

```sql
-- Main tables
snomed_brands          -- 89,447 records
snomed_generics        -- 9,870 records
snomed_products        -- 68,517 records
snomed_suppliers       -- 7,935 records
snomed_substances      -- 28,913 records
snomed_drug_forms      -- 423 records
snomed_routes          -- 161 records

-- Materialized view (performance)
snomed_drugs_complete  -- Pre-joined data
```

### Indexes

- **Full-text search** on brand names, generic names
- **GIN indexes** for fast text search
- **B-tree indexes** on foreign keys
- **Partial indexes** on active records

### Relationships

```
Substance → Generic → Brand → Product
                ↓
            Supplier
```

## 🔧 Manual Operations

### Refresh Materialized View

```sql
-- After bulk updates
SELECT refresh_snomed_complete_view();
```

### Check Data Quality

```sql
-- Brands without generic mapping
SELECT COUNT(*) FROM snomed_brands WHERE generic_id IS NULL;

-- Inactive brands
SELECT COUNT(*) FROM snomed_brands WHERE active = FALSE;

-- Top manufacturers
SELECT supplier_name, COUNT(*) as drug_count
FROM snomed_drugs_complete
GROUP BY supplier_name
ORDER BY drug_count DESC
LIMIT 10;
```

### Update Brand Status

```sql
-- Deactivate brand
UPDATE snomed_brands 
SET active = FALSE 
WHERE snomed_id = 2430421000189104;

-- Refresh view
SELECT refresh_snomed_complete_view();
```

## 📈 Performance

### Query Performance

| Operation | Response Time | Records |
|-----------|---------------|---------|
| Search | < 50ms | 89K brands |
| Autocomplete | < 20ms | 10 suggestions |
| Brand details | < 10ms | 1 record |
| Alternatives | < 30ms | 20 records |

### Optimization

- **Materialized view** for complex joins
- **GIN indexes** for text search
- **Batch loading** (5,000 records/batch)
- **Connection pooling** (20 connections)

## 🔄 Data Updates

### Manual Update

```bash
# Re-run ETL pipeline
python3 scripts/etl/load_snomed_data.py
```

### Automated Updates

```bash
# Setup cron job (weekly)
0 2 * * 0 /path/to/scripts/setup_snomed.sh >> /var/log/snomed_update.log 2>&1
```

## 🐛 Troubleshooting

### Issue: Data not loading

```bash
# Check file permissions
ls -la CommonDrugCodesForIndia_FlatFilePackage/

# Check database connection
psql -h localhost -U postgres -d medical_library -c "SELECT 1"

# Check logs
tail -f logs/snomed_etl.log
```

### Issue: Slow queries

```sql
-- Analyze query plan
EXPLAIN ANALYZE 
SELECT * FROM snomed_drugs_complete 
WHERE brand_name ILIKE '%metformin%';

-- Rebuild indexes
REINDEX TABLE snomed_brands;
VACUUM ANALYZE snomed_brands;
```

### Issue: Materialized view outdated

```sql
-- Check last refresh
SELECT * FROM snomed_etl_log ORDER BY created_at DESC LIMIT 1;

-- Manual refresh
SELECT refresh_snomed_complete_view();
```

## 📊 Monitoring

### ETL Logs

```sql
-- Check ETL history
SELECT * FROM snomed_etl_log 
ORDER BY created_at DESC 
LIMIT 10;

-- Failed records
SELECT table_name, records_failed, error_message
FROM snomed_etl_log
WHERE records_failed > 0;
```

### API Metrics

```bash
# Check search logs
tail -f logs/app.log | grep "snomed"

# Monitor response times
grep "response_time_ms" logs/app.log | awk '{sum+=$NF; count++} END {print sum/count}'
```

## 🎓 Best Practices

### 1. Always Use SNOMED IDs

```javascript
// ✅ Good - Use SNOMED ID
prescription.drug_id = 2430421000189104;

// ❌ Bad - Use text
prescription.drug_name = "Crocin 500mg";
```

### 2. Cache Frequently Accessed Data

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_brand_details(snomed_id: int):
    return db.query(SnomedBrand).filter_by(snomed_id=snomed_id).first()
```

### 3. Use Autocomplete for UX

```javascript
// Debounced autocomplete
const searchDrugs = debounce(async (query) => {
  const results = await fetch(`/api/v1/snomed/autocomplete?q=${query}`);
  showSuggestions(results);
}, 300);
```

### 4. Handle Alternatives Gracefully

```python
# Always check if alternatives exist
alternatives = get_alternatives(snomed_id)
if alternatives:
    show_substitution_options(alternatives)
else:
    show_no_alternatives_message()
```

## 🔐 Security

- ✅ API key authentication required
- ✅ Rate limiting enabled
- ✅ SQL injection prevention (parameterized queries)
- ✅ Input validation on all endpoints

## 📝 License

SNOMED CT data is provided under SNOMED International license. Ensure compliance with licensing terms for commercial use.

## 🆘 Support

- **Logs**: `logs/snomed_etl.log`, `logs/app.log`
- **Database**: Check `snomed_etl_log` table
- **API Docs**: http://localhost:8001/docs

---

**Built for Indian Healthcare Market** 🇮🇳
