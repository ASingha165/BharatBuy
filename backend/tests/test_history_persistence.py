"""
Regression tests for Procurement History Persistence and User Isolation.
Verifies:
A. Successful history save
B. Successful history retrieval
C. Authentication failure (unauthenticated access rejected with 401)
D. Firestore unavailable fallback (graceful local DB persistence)
E. Malformed/unsupported history fields rejected (Pydantic validation 422)
F. Empty history returns clean empty list
G. User isolation (User A cannot access or delete User B's history)
H. Single record deletion scoped by owner
I. Procurement analysis completes independently of history persistence
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.repositories.history_repository import (
    get_history_repository,
    ProcurementHistoryRepository,
    ProductionPersistenceError
)

client = TestClient(app)


def test_unauthenticated_history_save_rejected():
    """Requirement C: Unauthenticated save returns 401."""
    response = client.post(
        "/api/v1/procurement/history",
        json={
            "procurement_id": "proc-unauth-123",
            "company_name": "Solar Procurement",
            "request_status": "COMPLETED",
        },
    )
    assert response.status_code == 401
    assert "detail" in response.json()


def test_unauthenticated_history_get_rejected():
    """Requirement C: Unauthenticated retrieval returns 401."""
    response = client.get("/api/v1/procurement/history")
    assert response.status_code == 401


def test_successful_history_save_and_retrieval():
    """Requirement A & B: Successful save and retrieval for authenticated user."""
    user_uid = "uid_engineer_alpha"
    user_email = "engineer.alpha@bharatbuy.in"
    token = f"test_mock_token:{user_uid}:{user_email}"

    payload = {
        "procurement_id": "proc-solar-alpha-1",
        "company_name": "Zenith Solar Works",
        "request_status": "COMPLETED",
        "ai_provider": "deterministic_fallback",
        "request": {
            "title": "50kW Solar PV Rooftop Project",
            "requirements": [{"item": "Solar Module", "specifications": "540W Mono PERC"}],
        },
        "items": [
            {
                "item_name": "Solar Modules",
                "matched_standards": ["IS 14286", "IS/IEC 61730"],
            }
        ],
        "analysis": {
            "request_id": "REQ-SOLAR-001",
            "summary": {
                "decision": "READY",
                "procurement_readiness_score": 92.5,
                "standards_coverage": 100.0,
            },
        },
    }

    # 1. Save history
    save_resp = client.post(
        "/api/v1/procurement/history",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert save_resp.status_code == 200
    saved_data = save_resp.json()
    assert saved_data["success"] is True
    assert saved_data["procurement_id"] == "proc-solar-alpha-1"

    # 2. Retrieve history
    get_resp = client.get(
        "/api/v1/procurement/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 200
    items = get_resp.json()
    assert isinstance(items, list)
    matching = [item for item in items if item.get("procurement_id") == "proc-solar-alpha-1"]
    assert len(matching) == 1
    snapshot = matching[0]
    assert snapshot["company_name"] == "Zenith Solar Works"
    assert snapshot["analysis"]["request_id"] == "REQ-SOLAR-001"
    assert snapshot["request"]["title"] == "50kW Solar PV Rooftop Project"


def test_user_isolation_strictly_enforced():
    """Requirement: User A cannot see or delete User B's records."""
    token_a = "test_mock_token:uid_user_a:a@enterprise.in"
    token_b = "test_mock_token:uid_user_b:b@enterprise.in"

    item_a = {
        "procurement_id": "proc-user-a-exclusive",
        "company_name": "Alpha Substation Corp",
        "request_status": "COMPLETED",
        "request": {
            "title": "Substation XLPE Cables",
            "requirements": [{"item": "11kV XLPE underground cables"}],
        },
    }

    # Save as User A
    res = client.post(
        "/api/v1/procurement/history",
        json=item_a,
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res.status_code == 200

    # User B lists history - MUST NOT see User A's record
    res_b = client.get(
        "/api/v1/procurement/history",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_b.status_code == 200
    ids_seen_by_b = [x.get("procurement_id") for x in res_b.json()]
    assert "proc-user-a-exclusive" not in ids_seen_by_b

    # User B attempts to delete User A's record - MUST return 404
    del_res = client.delete(
        "/api/v1/procurement/history/proc-user-a-exclusive",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert del_res.status_code == 404

    # User A can delete their own record
    del_a = client.delete(
        "/api/v1/procurement/history/proc-user-a-exclusive",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert del_a.status_code == 200


def test_empty_history_returns_clean_list():
    """Requirement F: Empty history returns an empty list without errors."""
    token_fresh = "test_mock_token:uid_brand_new_user:fresh@bharatbuy.in"
    res = client.get(
        "/api/v1/procurement/history",
        headers={"Authorization": f"Bearer {token_fresh}"},
    )
    assert res.status_code == 200
    assert res.json() == []


def test_malformed_history_payload_validation():
    """Requirement E: Missing mandatory fields returns 422."""
    token = "test_mock_token:uid_user_malformed:malformed@enterprise.in"
    # Missing procurement_id
    res = client.post(
        "/api/v1/procurement/history",
        json={"company_name": "Steel Corp"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 422


def test_firestore_unavailable_graceful_fallback():
    """Requirement D: Even if Firestore throws an error, local persistence succeeds."""
    user_uid = "uid_offline_test"
    repo = get_history_repository()

    record = {
        "procurement_id": "proc-offline-fallback-01",
        "company_name": "Tata Steel Tubes",
        "request_status": "COMPLETED",
        "request": {
            "requirements": [{"item": "Fe 500D TMT Reinforcement Bars"}],
        },
    }

    # Simulate Firestore failure
    with patch("backend.app.services.firestore_service.firestore_service._get_client", side_effect=Exception("Firestore network unreachable")):
        saved = repo.save_snapshot(user_id=user_uid, firebase_uid=user_uid, record=record)
        assert saved is True

        # Verify retrieval works from repository
        user_history = repo.list_snapshots(user_id=user_uid, firebase_uid=user_uid)
        saved_items = [h for h in user_history if h.get("procurement_id") == "proc-offline-fallback-01"]
        assert len(saved_items) == 1
        assert saved_items[0]["company_name"] == "Tata Steel Tubes"


def test_procurement_analysis_succeeds_independently():
    """Requirement J: Procurement analysis endpoint succeeds with valid test authentication [Backend Test Mock Auth]."""
    token = "test_mock_token:uid_proc_test:test@enterprise.in"
    analysis_payload = {
        "company": "Zenith Solar Systems",
        "requirements": [
            {
                "item": "Solar PV module",
                "quantity": 10.0,
                "unit": "units",
                "specifications": "540W mono PERC tier-1 solar panel IS 14286",
                "required_certifications": ["IS 14286"],
            }
        ],
        "top_k_per_item": 5,
    }
    response = client.post(
        "/api/v1/procurement/analyze",
        json=analysis_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "package_evaluation" in data
    assert "items" in data
    assert len(data["items"]) > 0
    assert data["package_evaluation"]["overall_readiness_score"] > 0


def test_production_persistence_fails_without_durable_storage():
    """
    Production Safety Gate:
    production configuration + Firestore unavailable + PostgreSQL unavailable
    Expected:
    history persistence fails clearly with ProductionPersistenceError.
    It must NOT silently write to local SQLite.
    """
    repo = get_history_repository()
    user_uid = "uid_prod_safety_test"
    record = {
        "procurement_id": "proc-prod-safety-reject-01",
        "company_name": "Bharat Heavy Infra",
        "request_status": "COMPLETED",
        "request": {
            "requirements": [{"item": "IS 1786 Fe 500D TMT Rebars"}],
        },
    }

    # Simulate production environment without durable storage
    with patch.object(repo, "is_production", return_value=True), \
         patch.object(repo, "has_firestore", return_value=False), \
         patch.object(repo.manager, "_force_sqlite", True), \
         patch.object(repo.manager, "_custom_database_url", None):

        # 1. save_snapshot must raise ProductionPersistenceError
        with pytest.raises(ProductionPersistenceError) as exc_info:
            repo.save_snapshot(user_id=user_uid, firebase_uid=user_uid, record=record)
        assert "Production environment requires durable persistence" in str(exc_info.value)
        assert "Local SQLite persistence is strictly prohibited in production" in str(exc_info.value)

        # 2. Verify nothing was written to SQLite
        with repo.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM procurement_history WHERE procurement_id = ?", ("proc-prod-safety-reject-01",))
            count = cursor.fetchone()[0]
            assert count == 0, "Security violation: Record was silently written to SQLite in production!"

        # 3. list_snapshots must raise ProductionPersistenceError in production without durable store
        with pytest.raises(ProductionPersistenceError):
            repo.list_snapshots(user_id=user_uid, firebase_uid=user_uid)

        # 4. delete_snapshot must raise ProductionPersistenceError in production without durable store
        with pytest.raises(ProductionPersistenceError):
            repo.delete_snapshot(procurement_id="proc-prod-safety-reject-01", user_id=user_uid, firebase_uid=user_uid)

    # 5. API endpoint must return HTTP 503 error when repo raises in production
    token = "test_mock_token:uid_prod_safety_test:prod_safety@enterprise.in"
    with patch("backend.app.api.routes.procurement.history_repository.save_snapshot", side_effect=ProductionPersistenceError("Production requires durable persistence (Cloud Firestore or PostgreSQL/Neon). Local SQLite persistence is strictly prohibited in production.")):
        api_resp = client.post(
            "/api/v1/procurement/history",
            json=record,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert api_resp.status_code == 503
        assert "History persistence unavailable in production" in api_resp.json()["detail"]
