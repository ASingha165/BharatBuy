from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_recommend_endpoint_cables():
    payload = {
        "query": "Procurement of electrical cables for 1.1 kV power distribution",
        "top_k": 5
    }
    response = client.post("/api/v1/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "model" in data
    assert data["total_found"] > 0
    
    codes = [item["is_code"] for item in data["results"]]
    # IS 694, IS 1554, or IS 7098 should be present
    assert any("694" in c or "1554" in c or "7098" in c for c in codes)
    assert data.get("explanation") is not None

def test_recommend_endpoint_concrete():
    payload = {
        "query": "High strength Portland Pozzolana Cement and concrete mix design for bridge piers",
        "top_k": 5
    }
    response = client.post("/api/v1/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_found"] > 0
    codes = [item["is_code"] for item in data["results"]]
    assert any("456" in c or "10262" in c or "1489" in c for c in codes)


def test_recommend_endpoint_with_firebase_bearer_token():
    """Verifies that the /recommend endpoint accepts and processes verified Firebase Bearer token."""
    test_token = "test_mock_token:fb_uid_search_buyer:buyer.solar@enterprise.in"
    payload = {
        "query": "Crystalline silicon terrestrial photovoltaic solar panels",
        "top_k": 3
    }
    response = client.post(
        "/api/v1/recommend",
        json=payload,
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_found"] > 0
    codes = [item["is_code"] for item in data["results"]]
    # IS 14286 or IS/IEC 61215 should be found
    assert any("14286" in c or "61215" in c or "16221" in c for c in codes)


def test_frontend_api_interceptor_and_auth_guards():
    """
    Regression audit for frontend connectivity & auth integrity:
    1. frontend/lib/api.ts must contain an Axios request interceptor dynamically fetching fresh getIdToken().
    2. frontend/app/page.tsx handleSearch and handleProcurementSubmit must guard against SIGNED_OUT / INITIALIZING calls.
    """
    import os
    api_ts = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "lib", "api.ts")
    assert os.path.exists(api_ts), "frontend/lib/api.ts must exist"
    with open(api_ts, "r", encoding="utf-8") as f:
        api_content = f.read()

    assert "interceptors.request.use" in api_content, "apiClient must use request interceptor for dynamic token"
    assert "getIdToken" in api_content, "Interceptor must acquire fresh ID token"

    page_tsx = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "app", "page.tsx")
    assert os.path.exists(page_tsx), "frontend/app/page.tsx must exist"
    with open(page_tsx, "r", encoding="utf-8") as f:
        page_content = f.read()

    assert "authState !== 'SIGNED_IN'" in page_content, "page.tsx must guard against calling endpoints while signed out"

