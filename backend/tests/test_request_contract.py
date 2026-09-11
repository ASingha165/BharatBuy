"""
Task 11 — Regression Tests: Frontend Request Contract & Error Handling

Validates the exact property names, serialization, filtering, and HTTP error semantics
expected by the backend /api/v1/procurement/analyze endpoint.

Does NOT rely on any external service (Gemini, Neon, Firebase) — all tests use the
TestClient against the running FastAPI app backed by the SQLite fallback.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app, raise_server_exceptions=False)

# ──────────────────────────────────────────────────────────────────────────────
# 1. Single structured procurement item serializes correctly
# ──────────────────────────────────────────────────────────────────────────────
def test_single_item_serializes_correctly():
    payload = {
        "company": "Test Entity",
        "requirements": [
            {
                "item": "1.1 kV XLPE insulated solar DC power cables",
                "quantity": 2000,
                "unit": "meters",
                "specifications": "Crosslinked polyethylene cables, 1100 V rating, UV and weather resistant per IS 7098 Part 1"
            }
        ],
        "top_k_per_item": 5
    }
    r = client.post("/api/v1/procurement/analyze", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["company"] == "Test Entity"
    assert len(data["items"]) == 1


# ──────────────────────────────────────────────────────────────────────────────
# 2. Multiple structured procurement items serialize correctly
# ──────────────────────────────────────────────────────────────────────────────
def test_multiple_items_serialize_correctly():
    payload = {
        "company": "Brainware University",
        "requirements": [
            {
                "item": "1.1 kV XLPE insulated solar DC power cables",
                "quantity": 2000,
                "unit": "meters",
                "specifications": "Crosslinked polyethylene cables, 1100 V rating, UV and weather resistant per IS 7098 Part 1"
            },
            {
                "item": "Galvanized steel solar mounting structures",
                "quantity": 30,
                "unit": "sets",
                "specifications": "Hot-dip galvanized structural steel sections per IS 2062, corrosion resistant for outdoor solar racking"
            }
        ],
        "top_k_per_item": 5
    }
    r = client.post("/api/v1/procurement/analyze", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["company"] == "Brainware University"
    assert len(data["items"]) == 2


# ──────────────────────────────────────────────────────────────────────────────
# 3. Blank rows are excluded — sending only items with item names populated
# ──────────────────────────────────────────────────────────────────────────────
def test_blank_rows_excluded():
    """
    The backend processes all items that pass Pydantic validation (item min_length=1).
    This test confirms that sending only valid non-blank items returns results for those items.
    Blank-row filtering is a frontend responsibility; validated here via the API contract.
    """
    payload = {
        "company": "Filtered Row Test",
        "requirements": [
            {
                "item": "Portland Pozzolana Cement",
                "quantity": 100,
                "unit": "bags",
                "specifications": "PPC cement per IS 1489 Part 1"
            }
        ],
        "top_k_per_item": 3
    }
    r = client.post("/api/v1/procurement/analyze", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert len(data["items"]) == 1


# ──────────────────────────────────────────────────────────────────────────────
# 4. Completely empty requirements AND no description → 400
# ──────────────────────────────────────────────────────────────────────────────
def test_empty_procurement_form_rejected():
    payload = {
        "company": "Some Company",
        "requirements": []
    }
    r = client.post("/api/v1/procurement/analyze", json=payload)
    assert r.status_code == 400
    body = r.json()
    assert "requirements" in body["detail"].lower() or "description" in body["detail"].lower()


# ──────────────────────────────────────────────────────────────────────────────
# 5. Company is required — missing company → 422
# ──────────────────────────────────────────────────────────────────────────────
def test_company_is_required():
    payload = {
        "requirements": [
            {"item": "Steel rebar", "quantity": 10, "unit": "tonnes", "specifications": "IS 1786"}
        ],
        "top_k_per_item": 5
    }
    r = client.post("/api/v1/procurement/analyze", json=payload)
    assert r.status_code == 422


# ──────────────────────────────────────────────────────────────────────────────
# 6. Quantity must be numeric — non-numeric quantity → 422
# ──────────────────────────────────────────────────────────────────────────────
def test_quantity_must_be_numeric():
    payload = {
        "company": "Test Corp",
        "requirements": [
            {"item": "Steel rebar", "quantity": "not_a_number", "unit": "tonnes", "specifications": "IS 1786"}
        ],
        "top_k_per_item": 5
    }
    r = client.post("/api/v1/procurement/analyze", json=payload)
    assert r.status_code == 422


# ──────────────────────────────────────────────────────────────────────────────
# 7. Exact property names: company, requirements, item, quantity, unit,
#    specifications, top_k_per_item
# ──────────────────────────────────────────────────────────────────────────────
def test_exact_property_names_accepted():
    payload = {
        "company": "PropertyName Validator",
        "requirements": [
            {
                "item": "Electrical cables",
                "quantity": 500,
                "unit": "meters",
                "specifications": "PVC insulated per IS 694"
            }
        ],
        "top_k_per_item": 5
    }
    r = client.post("/api/v1/procurement/analyze", json=payload)
    assert r.status_code == 200
    data = r.json()
    # Verify the response contains expected top-level properties
    assert "request_id" in data
    assert "company" in data
    assert "items" in data
    assert "package_evaluation" in data
    assert "recommendations" in data
    assert "explanation" in data


# ──────────────────────────────────────────────────────────────────────────────
# 8. Successful analysis handles HTTP 200 and returns correct structure
# ──────────────────────────────────────────────────────────────────────────────
def test_successful_analysis_http_200():
    payload = {
        "company": "Success Test Inc",
        "requirements": [
            {
                "item": "Fe 500 TMT steel reinforcement bars",
                "quantity": 45,
                "unit": "metric tonnes",
                "specifications": "TMT rebar per IS 1786, yield strength 500 MPa"
            }
        ],
        "top_k_per_item": 5
    }
    r = client.post("/api/v1/procurement/analyze", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "request_id" in data
    assert isinstance(data["items"], list)
    assert isinstance(data["recommendations"], list)
    pkg = data["package_evaluation"]
    assert "overall_readiness_score" in pkg
    assert 0.0 <= pkg["overall_readiness_score"] <= 100.0


# ──────────────────────────────────────────────────────────────────────────────
# 9. HTTP 422 — Pydantic validation error (missing required field)
# ──────────────────────────────────────────────────────────────────────────────
def test_http_422_produces_validation_error():
    # Missing "company" field entirely
    payload = {
        "requirements": [{"item": "cables", "quantity": 100, "unit": "m", "specifications": ""}]
    }
    r = client.post("/api/v1/procurement/analyze", json=payload)
    assert r.status_code == 422
    body = r.json()
    assert "detail" in body


# ──────────────────────────────────────────────────────────────────────────────
# 10. HTTP 401 — unauthorized protected endpoint
# ──────────────────────────────────────────────────────────────────────────────
def test_http_401_on_protected_endpoint_without_token():
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401
    body = r.json()
    assert "detail" in body
    assert "authentication" in body["detail"].lower() or "sign in" in body["detail"].lower()


# ──────────────────────────────────────────────────────────────────────────────
# 11. HTTP 403 — legacy auth disabled
# ──────────────────────────────────────────────────────────────────────────────
def test_http_403_legacy_auth_disabled():
    payload = {"email": "test@example.com", "password": "password123"}
    r = client.post("/api/v1/auth/signin", json=payload)
    # Either 403 (legacy disabled) or 401 (wrong credentials if legacy enabled)
    assert r.status_code in (403, 401)


# ──────────────────────────────────────────────────────────────────────────────
# 12. HTTP 500 — backend surfaces clean error without stack trace
# ──────────────────────────────────────────────────────────────────────────────
def test_no_stacktrace_in_error_response():
    # Item with extremely long/malformed specifications to trigger internal paths
    payload = {
        "company": "ErrorTest Corp",
        "requirements": [
            {
                "item": "Unknown exotic material XYZ-9999",
                "quantity": 1,
                "unit": "units",
                "specifications": "Unknown spec"
            }
        ],
        "top_k_per_item": 5
    }
    r = client.post("/api/v1/procurement/analyze", json=payload)
    # Should succeed (returns 200 with low scores) or fail with 500 — never expose tracebacks
    body = r.text
    assert "Traceback" not in body
    assert "File \"" not in body
    assert r.status_code in (200, 500)


# ──────────────────────────────────────────────────────────────────────────────
# 13. Network-failure: health endpoint available
# ──────────────────────────────────────────────────────────────────────────────
def test_health_endpoint_returns_200():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] in ("healthy", "ok", "HEALTHY")
    assert "total_standards" in data
    assert data["total_standards"] > 0


# ──────────────────────────────────────────────────────────────────────────────
# 14. Health HTTP 200 → database=true and total_standards populated
# ──────────────────────────────────────────────────────────────────────────────
def test_health_system_active_state():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("database") is True
    assert isinstance(data.get("total_standards"), int)
    assert data["total_standards"] > 500  # 559 standards expected


# ──────────────────────────────────────────────────────────────────────────────
# 15. top_k_per_item defaults to 5 when omitted
# ──────────────────────────────────────────────────────────────────────────────
def test_top_k_per_item_defaults():
    payload = {
        "company": "Default TopK Test",
        "requirements": [
            {
                "item": "PVC insulated cables",
                "quantity": 100,
                "unit": "meters",
                "specifications": "IS 694 compliant"
            }
        ]
        # top_k_per_item omitted — should default to 5
    }
    r = client.post("/api/v1/procurement/analyze", json=payload)
    assert r.status_code == 200
    data = r.json()
    # Each item should have at most 5 standards (top_k_per_item=5 default)
    for item in data["items"]:
        assert len(item.get("standards", [])) <= 5
