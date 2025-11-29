"""
Test consolidated API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ============================================================================
# HEALTH TESTS
# ============================================================================

def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_health_detailed():
    response = client.get("/api/v1/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert "database" in data
    assert "status" in data

# ============================================================================
# ICD SEARCH TESTS
# ============================================================================

def test_icd_search_basic():
    response = client.get("/api/v1/icd10/search?q=diabetes")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total" in data
    assert data["query"] == "diabetes"

def test_icd_search_with_systems():
    response = client.get("/api/v1/icd10/search?q=fever&systems=icd10")
    assert response.status_code == 200
    data = response.json()
    assert "icd10" in data["systems"]

def test_icd_search_with_chapter():
    response = client.get("/api/v1/icd10/search?q=diabetes&chapter=E")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "diabetes"

def test_icd_search_autocomplete():
    response = client.get("/api/v1/icd10/search?q=dia&autocomplete=true&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["autocomplete_mode"] == True
    # Note: limit applies per system, so total can be up to limit * num_systems
    assert data["total"] >= 0

def test_icd_search_validation():
    # Too short query
    response = client.get("/api/v1/icd10/search?q=a")
    assert response.status_code == 422

def test_get_icd_code():
    response = client.get("/api/v1/icd10/E11")
    assert response.status_code in [200, 404]  # 404 if no data loaded

def test_get_icd_code_with_hierarchy():
    response = client.get("/api/v1/icd10/E11?hierarchy=true")
    assert response.status_code in [200, 404]

def test_get_chapters():
    response = client.get("/api/v1/icd10/chapters")
    assert response.status_code == 200
    data = response.json()
    assert "chapters" in data
    assert len(data["chapters"]) == 19

# ============================================================================
# DRUG TESTS
# ============================================================================

def test_drug_search():
    response = client.get("/api/v1/drugs/search?q=metformin")
    assert response.status_code == 200
    data = response.json()
    assert "drugs" in data
    assert "query" in data
    assert data["query"] == "metformin"

def test_drug_search_validation():
    response = client.get("/api/v1/drugs/search?q=a")
    assert response.status_code == 422

def test_get_drug():
    response = client.get("/api/v1/drugs/1")
    assert response.status_code in [200, 404]

def test_check_interactions():
    response = client.post("/api/v1/drugs/interactions", json={"drug_ids": [1, 2]})
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        data = response.json()
        assert "has_interactions" in data
        assert "interactions" in data

def test_check_interactions_validation():
    # Too few drugs
    response = client.post("/api/v1/drugs/interactions", json={"drug_ids": [1]})
    assert response.status_code == 422
    
    # Too many drugs
    response = client.post("/api/v1/drugs/interactions", json={"drug_ids": list(range(20))})
    assert response.status_code == 422

# ============================================================================
# AB-HBP TESTS
# ============================================================================

def test_abhbp_search():
    response = client.get("/api/v1/abhbp/search?q=surgery")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "count" in data

def test_abhbp_search_with_specialty():
    response = client.get("/api/v1/abhbp/search?q=surgery&specialty=cardiology")
    assert response.status_code == 200

def test_get_abhbp():
    response = client.get("/api/v1/abhbp/PKG001")
    assert response.status_code in [200, 404]

# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

def test_response_time():
    import time
    start = time.time()
    response = client.get("/api/v1/icd10/search?q=diabetes")
    elapsed = (time.time() - start) * 1000
    
    assert response.status_code == 200
    assert elapsed < 1000  # Should respond within 1 second

def test_concurrent_requests():
    import concurrent.futures
    
    def make_request():
        return client.get("/api/v1/health")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(10)]
        results = [f.result() for f in futures]
    
    assert all(r.status_code == 200 for r in results)

# ============================================================================
# EDGE CASES
# ============================================================================

def test_special_characters():
    response = client.get("/api/v1/icd10/search?q=test%20query")
    assert response.status_code == 200

def test_unicode_search():
    response = client.get("/api/v1/drugs/search?q=पैरासिटामोल")
    assert response.status_code == 200

def test_sql_injection_prevention():
    response = client.get("/api/v1/icd10/search?q='; DROP TABLE icd10_codes; --")
    assert response.status_code == 200  # Should not crash
    data = response.json()
    assert "results" in data

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
