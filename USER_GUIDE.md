# 📖 HMS Terminology Service - User Guide

Complete guide for using the HMS Terminology Service API with SNOMED CT Indian Drug Database.

---

## 🚀 Getting Started

### Prerequisites
- API Key (get from admin)
- HTTP client (curl, Postman, or code)
- Base URL: `http://localhost:8001`

### Authentication
All endpoints require API key in header:
```bash
X-API-Key: your-api-key-here
```

---

## 🏥 Use Cases

### 1. Doctor Prescribing Drugs

**Scenario**: Doctor searches for "metformin" to prescribe

```bash
# Step 1: Search for drug
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/search?q=metformin&page_size=10"
```

**Response**:
```json
{
  "query": "metformin",
  "total": 523,
  "page": 1,
  "page_size": 10,
  "results": [
    {
      "snomed_id": 2430421000189104,
      "brand_name": "Glycomet 500mg Tablet",
      "generic_name": "Metformin",
      "supplier_name": "USV Ltd",
      "indication": "Type 2 Diabetes",
      "license_status": "APPROVED"
    }
  ]
}
```

```bash
# Step 2: Get full details
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/brands/2430421000189104"
```

**What to store in prescription**:
- `snomed_id`: 2430421000189104 (unique identifier)
- `brand_name`: "Glycomet 500mg Tablet"
- `generic_name`: "Metformin"

---

### 2. Pharmacy Substitution

**Scenario**: Pharmacy needs cheaper alternative for prescribed drug

```bash
# Get alternatives for prescribed drug
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/brands/2430421000189104/alternatives?limit=20"
```

**Response**:
```json
[
  {
    "snomed_id": 2430431000189102,
    "brand_name": "Glyciphage 500mg Tablet",
    "supplier_name": "Lupin Ltd",
    "license_status": "APPROVED",
    "same_generic": true
  },
  {
    "snomed_id": 2430441000189105,
    "brand_name": "Metsmall 500mg Tablet",
    "supplier_name": "Ajanta Pharma",
    "license_status": "APPROVED",
    "same_generic": true
  }
]
```

**Use case**: Show patient cheaper options with same active ingredient

---

### 3. Insurance Claim Validation

**Scenario**: Validate if prescribed drug is in approved list

```bash
# Step 1: Get drug details by SNOMED ID from claim
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/brands/2430421000189104"
```

**Validation checks**:
- `license_status`: Must be "APPROVED"
- `active`: Must be true
- `generic_name`: Match against approved generics list

---

### 4. Drug Inventory Management

**Scenario**: Get all drugs from a specific manufacturer

```bash
# Step 1: Search for manufacturer
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/search?q=USV+Ltd"

# Step 2: Get supplier details
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/suppliers/1058411000189103"

# Step 3: Get all drugs by supplier
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/suppliers/1058411000189103/drugs?page_size=100"
```

---

### 5. Clinical Decision Support

**Scenario**: Find all brands for a specific generic formulation

```bash
# Step 1: Search for generic
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/search?q=metformin"

# Step 2: Get generic details
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/generics/1321000189104"

# Step 3: Get all brands with this generic
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/generics/1321000189104/brands?page_size=50"
```

---

## 📡 API Endpoints Reference

### Drug Search

#### Search Drugs
```
GET /api/v1/snomed/search
```

**Parameters**:
- `q` (required): Search query (brand, generic, indication)
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Results per page (default: 20, max: 100)
- `filter_active` (optional): Filter active drugs only (default: true)

**Example**:
```bash
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/search?q=paracetamol&page=1&page_size=20"
```

---

#### Autocomplete
```
GET /api/v1/snomed/autocomplete
```

**Parameters**:
- `q` (required): Search prefix (min 2 chars)
- `limit` (optional): Max suggestions (default: 10, max: 50)

**Example**:
```bash
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/autocomplete?q=cro&limit=10"
```

**Response**:
```json
{
  "query": "cro",
  "suggestions": [
    {"name": "Crocin 500mg Tablet", "type": "brand"},
    {"name": "Crocin Advance", "type": "brand"},
    {"name": "Cromal", "type": "brand"}
  ]
}
```

---

### Brand Operations

#### Get Brand Details
```
GET /api/v1/snomed/brands/{snomed_id}
```

**Example**:
```bash
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/brands/2430421000189104"
```

---

#### Find Alternatives
```
GET /api/v1/snomed/brands/{snomed_id}/alternatives
```

**Parameters**:
- `limit` (optional): Max alternatives (default: 20, max: 100)

**Example**:
```bash
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/brands/2430421000189104/alternatives?limit=10"
```

---

### Generic Operations

#### Get Generic Details
```
GET /api/v1/snomed/generics/{snomed_id}
```

**Example**:
```bash
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/generics/1321000189104"
```

---

#### Get Brands by Generic
```
GET /api/v1/snomed/generics/{snomed_id}/brands
```

**Parameters**:
- `page` (optional): Page number
- `page_size` (optional): Results per page

**Example**:
```bash
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/generics/1321000189104/brands?page_size=50"
```

---

### Supplier Operations

#### Get Supplier Details
```
GET /api/v1/snomed/suppliers/{snomed_id}
```

**Example**:
```bash
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/suppliers/1058411000189103"
```

---

#### Get Drugs by Supplier
```
GET /api/v1/snomed/suppliers/{snomed_id}/drugs
```

**Parameters**:
- `page` (optional): Page number
- `page_size` (optional): Results per page

---

### Statistics

#### Get Database Stats
```
GET /api/v1/snomed/stats
```

**Example**:
```bash
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/stats"
```

**Response**:
```json
{
  "active_brands": 89446,
  "total_brands": 89446,
  "total_generics": 9869,
  "active_suppliers": 7934,
  "total_products": 68516,
  "total_substances": 28912,
  "last_updated": "2024-12-17",
  "coverage": "89,447 Indian brands with SNOMED CT codes"
}
```

---

## 💻 Code Examples

### Python

```python
import requests

API_BASE = "http://localhost:8001"
API_KEY = "dev-key-123"

headers = {"X-API-Key": API_KEY}

# Search drugs
response = requests.get(
    f"{API_BASE}/api/v1/snomed/search",
    params={"q": "metformin", "page_size": 10},
    headers=headers
)
drugs = response.json()

# Get brand details
brand_id = drugs["results"][0]["snomed_id"]
response = requests.get(
    f"{API_BASE}/api/v1/snomed/brands/{brand_id}",
    headers=headers
)
brand = response.json()

# Find alternatives
response = requests.get(
    f"{API_BASE}/api/v1/snomed/brands/{brand_id}/alternatives",
    params={"limit": 20},
    headers=headers
)
alternatives = response.json()
```

---

### JavaScript

```javascript
const API_BASE = "http://localhost:8001";
const API_KEY = "dev-key-123";

const headers = {
  "X-API-Key": API_KEY
};

// Search drugs
async function searchDrugs(query) {
  const response = await fetch(
    `${API_BASE}/api/v1/snomed/search?q=${query}&page_size=10`,
    { headers }
  );
  return await response.json();
}

// Get brand details
async function getBrandDetails(snomedId) {
  const response = await fetch(
    `${API_BASE}/api/v1/snomed/brands/${snomedId}`,
    { headers }
  );
  return await response.json();
}

// Find alternatives
async function findAlternatives(snomedId) {
  const response = await fetch(
    `${API_BASE}/api/v1/snomed/brands/${snomedId}/alternatives?limit=20`,
    { headers }
  );
  return await response.json();
}

// Usage
const drugs = await searchDrugs("metformin");
const brand = await getBrandDetails(drugs.results[0].snomed_id);
const alternatives = await findAlternatives(brand.snomed_id);
```

---

### cURL

```bash
# Search
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/search?q=metformin"

# Brand details
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/brands/2430421000189104"

# Alternatives
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/brands/2430421000189104/alternatives"
```

---

## 🎯 Best Practices

### 1. Always Use SNOMED IDs

✅ **Good**:
```json
{
  "prescription": {
    "drug_snomed_id": 2430421000189104,
    "drug_name": "Glycomet 500mg"
  }
}
```

❌ **Bad**:
```json
{
  "prescription": {
    "drug_name": "Glycomet 500mg"
  }
}
```

### 2. Implement Autocomplete

```javascript
// Debounced autocomplete
const searchInput = document.getElementById('drug-search');
let timeout;

searchInput.addEventListener('input', (e) => {
  clearTimeout(timeout);
  timeout = setTimeout(async () => {
    const query = e.target.value;
    if (query.length >= 2) {
      const suggestions = await fetch(
        `${API_BASE}/api/v1/snomed/autocomplete?q=${query}`,
        { headers }
      ).then(r => r.json());
      showSuggestions(suggestions);
    }
  }, 300);
});
```

### 3. Handle Pagination

```python
def get_all_brands_for_generic(generic_id):
    all_brands = []
    page = 1
    
    while True:
        response = requests.get(
            f"{API_BASE}/api/v1/snomed/generics/{generic_id}/brands",
            params={"page": page, "page_size": 100},
            headers=headers
        )
        data = response.json()
        all_brands.extend(data)
        
        if len(data) < 100:
            break
        page += 1
    
    return all_brands
```

### 4. Cache Frequently Accessed Data

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_brand_details(snomed_id):
    response = requests.get(
        f"{API_BASE}/api/v1/snomed/brands/{snomed_id}",
        headers=headers
    )
    return response.json()
```

### 5. Error Handling

```javascript
async function searchDrugs(query) {
  try {
    const response = await fetch(
      `${API_BASE}/api/v1/snomed/search?q=${query}`,
      { headers }
    );
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Search failed:', error);
    return { results: [], error: error.message };
  }
}
```

---

## ⚠️ Common Errors

### 401 Unauthorized
```json
{"detail": "Invalid API key"}
```
**Solution**: Check API key in header

### 404 Not Found
```json
{"detail": "Brand with SNOMED ID 999999 not found"}
```
**Solution**: Verify SNOMED ID exists

### 422 Validation Error
```json
{"detail": "Query must be at least 2 characters"}
```
**Solution**: Check request parameters

### 429 Too Many Requests
```json
{"detail": "Rate limit exceeded"}
```
**Solution**: Implement rate limiting in client

---

## 📊 Performance Tips

1. **Use pagination** - Don't fetch all results at once
2. **Implement caching** - Cache frequently accessed data
3. **Use autocomplete** - Reduce full searches
4. **Batch requests** - Combine multiple lookups when possible
5. **Filter active only** - Use `filter_active=true` parameter

---

## 🔗 Additional Resources

- **API Documentation**: http://localhost:8001/docs
- **SNOMED Integration Guide**: docs/SNOMED_INTEGRATION.md
- **Migration Guide**: docs/SNOMED_MIGRATION_GUIDE.md
- **Quick Start**: SNOMED_QUICKSTART.md

---

## 🆘 Support

**Issues?**
- Check logs: `logs/app.log`
- API health: `GET /api/v1/health`
- Database stats: `GET /api/v1/snomed/stats`

**Contact**: support@example.com

---

**Built for Indian Healthcare Market** 🇮🇳
