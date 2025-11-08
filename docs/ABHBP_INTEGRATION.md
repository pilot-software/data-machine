# 🏥 Ayushman Bharat HBP Integration

## Overview
Integration of Ayushman Bharat Health Benefit Package (AB-HBP) procedure codes into HMS Terminology Service.

## Data Source
**Official Excel**: https://ayushmanbharat.mp.gov.in/uploads/media/HBP_2022_Package_Master1.xlsx

## Setup

### 1. Database Setup
```bash
psql -d hms_terminology -f scripts/setup_drug_db.sql
```

### 2. Download Data
```bash
python scripts/etl/download_abhbp_data.py
```

### 3. Load Data
```bash
python scripts/etl/load_abhbp_data.py
```

## API Endpoints

### Search Procedures
```bash
GET /api/v1/abhbp/search?q=appendectomy
GET /api/v1/abhbp/search?q=knee&specialty=Orthopedics
```

### Get Procedure Details
```bash
GET /api/v1/abhbp/1.1.1
```

### List Specialties
```bash
GET /api/v1/abhbp/specialties/list
```

## Response Format

```json
{
  "count": 1,
  "results": [
    {
      "package_code": "1.1.1",
      "package_name": "Appendectomy",
      "specialty": "General Surgery",
      "base_rate": 10000.00,
      "procedure_type": "Surgical",
      "preauth_required": false
    }
  ]
}
```

## Features

✅ 1,949+ procedure packages  
✅ 27 specialties  
✅ Full-text search  
✅ ICD-10 mapping ready  
✅ Rate information  

## Integration Points

- **ICD-10**: Link procedures to diagnosis codes
- **Drugs**: Connect procedures to required medications
- **Pricing**: HBP rates for empaneled hospitals

## Auto-Update

Add to cron for quarterly updates:
```bash
0 0 1 */3 * cd /path/to/project && python scripts/etl/download_abhbp_data.py && python scripts/etl/load_abhbp_data.py
```
