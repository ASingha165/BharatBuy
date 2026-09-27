import pytest
import time
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.requests import ProcurementAnalysisRequest, ProcurementRequirementItem

client = TestClient(app)

def test_health_check_responds_rapidly():
    """Verifies that GET /api/v1/health responds under 1 second without stalling."""
    t0 = time.time()
    response = client.get("/api/v1/health")
    elapsed = time.time() - t0
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] is True
    assert data["total_standards"] == 559
    assert elapsed < 1.0, f"Health check took {elapsed:.2f}s, expected < 1.0s"

def test_docs_endpoint_accessible():
    """Verifies that GET /docs works and does not return 404."""
    response = client.get("/docs", follow_redirects=True)
    assert response.status_code == 200

def test_procurement_analyze_unauthenticated_returns_401():
    """Verifies that POST /api/v1/procurement/analyze rejects unauthenticated calls with 401."""
    payload = {
        "company": "Solar India Ltd",
        "requirements": [{"item": "cable", "quantity": 1, "unit": "unit"}]
    }
    resp = client.post("/api/v1/procurement/analyze", json=payload)
    assert resp.status_code == 401

def test_procurement_analyze_authenticated_succeeds():
    """
    Verifies that POST /api/v1/procurement/analyze and alias /api/procurement/analyze
    execute rapidly with valid authentication.
    """
    token = "test_mock_token:usr_resilience:buyer@test.in"
    auth_headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "company": "Solar India Ltd",
        "requirements": [
            {
                "item": "1.1 kV XLPE insulated electrical cables",
                "quantity": 500,
                "unit": "meters",
                "specifications": "Crosslinked polyethylene cables, 1100 V rating, IS 7098 Part 1"
            }
        ]
    }
    
    # 1. Main endpoint
    t0 = time.time()
    resp1 = client.post("/api/v1/procurement/analyze", json=payload, headers=auth_headers)
    elapsed1 = time.time() - t0
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert len(data1["items"]) == 1
    assert data1["package_evaluation"]["overall_readiness_score"] > 0
    assert elapsed1 < 15.0

    # 2. Alias endpoint
    t1 = time.time()
    resp2 = client.post("/api/procurement/analyze", json=payload, headers=auth_headers)
    elapsed2 = time.time() - t1
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert len(data2["items"]) == 1
    assert elapsed2 < 15.0

def test_standards_repository_caching():
    """Verifies that StandardsRepository in-memory cache makes repeated catalog fetches instantaneous."""
    from backend.app.api.dependencies import repository
    t0 = time.time()
    stds1 = repository.get_all_standards()
    t1 = time.time()
    stds2 = repository.get_all_standards()
    t2 = time.time()
    
    assert len(stds1) == 559
    assert len(stds2) == 559
    # Second fetch must be instant from cache
    assert (t2 - t1) < 0.01, f"Cached fetch took {t2-t1:.4f}s, expected < 0.01s"
