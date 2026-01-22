# Database Cleanup Summary

## Removed Tables (6 total)

### 1. `loinc` - Lab Test Codes
- **Reason**: Not mentioned in core features, no active endpoints
- **Impact**: None - not used in application

### 2. `symptoms_master` - Symptom Dictionary
- **Reason**: No endpoints using this table
- **Impact**: None - not referenced in code

### 3. `abhbp_procedures` - Ayushman Bharat HBP
- **Reason**: Not in core features (README lists only ICD-10, drugs, AI)
- **Impact**: Removed `/api/v1/abhbp/*` endpoints
- **Files removed**: `app/api/abhbp_endpoints.py`

### 4. `snomed_drug_forms` - Drug Form Master
- **Reason**: Not actively used in queries
- **Impact**: None - data embedded in generics table

### 5. `snomed_routes` - Route of Administration
- **Reason**: Not actively used in queries
- **Impact**: None - data embedded in generics table

### 6. `snomed_etl_log` - ETL Logging
- **Reason**: Runtime logging not needed
- **Impact**: None - development/import only

## Retained Core Tables (6 total)

✅ **icd10_codes** - 71,704 diagnosis codes  
✅ **snomed_brands** - 89,446 Indian drug brands  
✅ **snomed_generics** - 9,869 generic formulations  
✅ **snomed_products** - Product catalog  
✅ **snomed_suppliers** - 7,934 manufacturers  
✅ **snomed_substances** - Chemical substances  

## Code Changes

### Modified Files
- `app/db/models.py` - Removed LOINC, SymptomMaster, ABHBPProcedure models
- `app/models/snomed_models.py` - Removed SnomedDrugForm, SnomedRoute, SnomedETLLog models
- `app/main.py` - Removed abhbp_router import and registration

### Deleted Files
- `app/api/abhbp_endpoints.py` - ABHBP API endpoints

## How to Execute Cleanup

```bash
# Run the cleanup script
./cleanup_db.sh

# Or manually
psql -U postgres -d medical_library -f scripts/cleanup_unused_tables.sql
```

## Rollback (if needed)

If you need to restore these tables, re-import the original database dump:

```bash
./import_database.sh database_dumps/hms_database_20260115_192253.tar.gz
```

## Database Size Impact

Estimated space savings: ~5-10% depending on ABHBP and LOINC data volume.

Run `\dt+` in psql to see table sizes before/after cleanup.
