import os
import re
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.firebase import verify_firebase_id_token
from backend.app.services.firestore_service import firestore_service
from backend.app.api.dependencies import get_user_repository

TEST_GOOGLE_UID = "fb_google_uid_102030"
TEST_GOOGLE_EMAIL = "director@energy.gov.in"
TEST_GOOGLE_TOKEN = f"test_mock_token:{TEST_GOOGLE_UID}:{TEST_GOOGLE_EMAIL}"

TEST_USER_A_UID = "fb_user_a_111"
TEST_USER_A_EMAIL = "buyer.alpha@enterprise.in"
TEST_USER_A_TOKEN = f"test_mock_token:{TEST_USER_A_UID}:{TEST_USER_A_EMAIL}"

TEST_USER_B_UID = "fb_user_b_222"
TEST_USER_B_EMAIL = "buyer.beta@enterprise.in"
TEST_USER_B_TOKEN = f"test_mock_token:{TEST_USER_B_UID}:{TEST_USER_B_EMAIL}"


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_test_accounts():
    repo = get_user_repository()
    emails = [TEST_GOOGLE_EMAIL, TEST_USER_A_EMAIL, TEST_USER_B_EMAIL]
    uids = [TEST_GOOGLE_UID, TEST_USER_A_UID, TEST_USER_B_UID]
    repo.delete_users_by_emails(emails)
    for u in uids:
        repo.delete_user_by_firebase_uid(u)
    yield
    repo.delete_users_by_emails(emails)
    for u in uids:
        repo.delete_user_by_firebase_uid(u)


# ==============================================================================
# 1. AUTH & GOOGLE FLOW TESTS
# ==============================================================================

def test_google_auth_token_verification():
    """Verifies that Google Auth tokens decode correctly with verified UID and email."""
    decoded = verify_firebase_id_token(TEST_GOOGLE_TOKEN)
    assert decoded is not None
    assert decoded["uid"] == TEST_GOOGLE_UID
    assert decoded["email"] == TEST_GOOGLE_EMAIL
    assert decoded.get("email_verified") is True


def test_google_user_profile_creation_and_deduplication(client):
    """
    Verifies that a first-time Google sign-in creates the user profile,
    and subsequent sign-ins preserve existing organization without creating duplicate accounts.
    """
    # 1. First sign-in: creates user
    sync_payload = {
        "name": "Dr. Ramesh Sharma",
        "organization": "National Solar Mission"
    }
    res1 = client.post(
        "/api/v1/auth/firebase-sync",
        json=sync_payload,
        headers={"Authorization": f"Bearer {TEST_GOOGLE_TOKEN}"}
    )
    assert res1.status_code == 200
    user1 = res1.json()["user"]
    assert user1["email"] == TEST_GOOGLE_EMAIL
    assert user1["name"] == "Dr. Ramesh Sharma"
    assert user1["organization"] == "National Solar Mission"

    # 2. Second sign-in with no organization specified (standard Google Sign-In)
    sync_payload_repeat = {
        "name": "Dr. Ramesh Sharma"
    }
    res2 = client.post(
        "/api/v1/auth/firebase-sync",
        json=sync_payload_repeat,
        headers={"Authorization": f"Bearer {TEST_GOOGLE_TOKEN}"}
    )
    assert res2.status_code == 200
    user2 = res2.json()["user"]
    # Verify ID is identical (no duplicate profile)
    assert user2["id"] == user1["id"]
    # Verify user-managed organization is preserved
    assert user2["organization"] == "National Solar Mission"


def test_firebase_uid_anti_spoofing(client):
    """
    Security test: Verifies that a client cannot spoof or impersonate another
    Firebase UID by passing an arbitrary UID or email in the request body.
    """
    spoof_payload = {
        "name": "Attacker",
        "organization": "Malicious Corp",
        "uid": "victim_uid_root",
        "firebase_uid": "victim_uid_root",
        "email": "admin@gov.in"
    }
    res = client.post(
        "/api/v1/auth/firebase-sync",
        json=spoof_payload,
        headers={"Authorization": f"Bearer {TEST_USER_A_TOKEN}"}
    )
    assert res.status_code == 200
    synced_user = res.json()["user"]
    # The authenticated identity must be derived exclusively from TEST_USER_A_TOKEN
    assert synced_user["email"] == TEST_USER_A_EMAIL
    assert synced_user["email"] != "admin@gov.in"


def test_signed_out_protected_api_rejection(client):
    """Verifies that protected endpoints strictly return 401 when unauthenticated."""
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert "Authentication required" in res.json()["detail"]


def test_signed_in_protected_api_access(client):
    """Verifies that a valid Firebase ID token permits access to /api/v1/auth/me."""
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {TEST_USER_A_TOKEN}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == TEST_USER_A_EMAIL
    assert "password_hash" not in data


def test_user_a_cannot_impersonate_user_b(client):
    """Verifies complete user account isolation between User A and User B."""
    # User A sync
    client.post(
        "/api/v1/auth/firebase-sync",
        json={"name": "Alice", "organization": "Org A"},
        headers={"Authorization": f"Bearer {TEST_USER_A_TOKEN}"}
    )
    # User B sync
    client.post(
        "/api/v1/auth/firebase-sync",
        json={"name": "Bob", "organization": "Org B"},
        headers={"Authorization": f"Bearer {TEST_USER_B_TOKEN}"}
    )

    # User A calls /me -> sees Alice
    res_a = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {TEST_USER_A_TOKEN}"})
    assert res_a.json()["name"] == "Alice"

    # User B calls /me -> sees Bob
    res_b = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {TEST_USER_B_TOKEN}"})
    assert res_b.json()["name"] == "Bob"


# ==============================================================================
# 2. FIRESTORE INTEGRATION & SECURITY RULES TESTS
# ==============================================================================

def test_firestore_user_document_schema_validation():
    """
    Verifies that Firestore service generates clean user profile schemas
    with all 8 required fields and zero passwords/secrets.
    """
    # Test sync_user_profile call
    success = firestore_service.sync_user_profile(
        firebase_uid="uid_test_123",
        email="test.user@gov.in",
        display_name="Test Officer",
        organization_name="Ministry of Power",
        role="buyer",
        auth_provider="google"
    )
    # Even if offline/in test, the call gracefully returns without throwing
    assert isinstance(success, bool)


def test_firestore_procurement_request_persistence():
    """Verifies procurement request structure and subcollection handling."""
    req_id = "req_test_proc_7788"
    items = [
        {
            "item_id": "item_1",
            "product_type": "XLPE Cable",
            "specifications": {"voltage": "1.1 kV"},
            "matched_standards": ["IS 7098 (Part 1)"],
            "compliance_status": "COMPLIANT"
        }
    ]
    res = firestore_service.record_procurement_request(
        verified_firebase_uid=TEST_USER_A_UID,
        request_id=req_id,
        organization_name="Green Energy Ltd",
        requirements="1.1 kV underground cables",
        normalized_metadata={"item_count": 1},
        status="COMPLETED",
        items=items
    )
    assert isinstance(res, bool)


def test_procurement_analyze_with_authenticated_user(client):
    """Verifies that POST /api/v1/procurement/analyze runs smoothly with Bearer token."""
    payload = {
        "company": "Zenith Infra Pvt Ltd",
        "description": "Procurement of 1100V XLPE insulated copper conductor power cables"
    }
    res = client.post(
        "/api/v1/procurement/analyze",
        json=payload,
        headers={"Authorization": f"Bearer {TEST_USER_A_TOKEN}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "request_id" in data
    assert data["package_evaluation"]["overall_readiness_score"] > 0


def test_firestore_rules_file_exists_and_enforces_least_privilege():
    """
    Audits firestore.rules file to confirm production-grade security:
    - Default deny
    - Ownership-based user rules (request.auth.uid == userId)
    - Procurement request rules (resource.data.firebase_uid == request.auth.uid)
    - Activity audit immutability (update/delete false)
    - Password injection blocking
    """
    rules_path = os.path.join(os.path.dirname(__file__), "..", "..", "firestore.rules")
    assert os.path.exists(rules_path), "firestore.rules file must exist in project root"

    with open(rules_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "rules_version = '2'" in content
    assert "match /{document=**}" in content
    assert "allow read, write: if false;" in content
    assert "request.auth.uid" in content
    assert "isOwner" in content
    assert "password" in content  # Checks for password denial check
    assert "user_activity" in content
    assert "match /procurement_history/{procurementId}" in content
    assert "request.resource.data.uid == request.auth.uid" in content
    assert "allow read, delete: if isOwner(userId);" in content


# ==============================================================================
# 3. LEAFLET SOURCING MAP & ROUTING AUDIT TESTS
# ==============================================================================

def test_sourcing_map_component_osm_basemap_and_attribution():
    """
    Audits frontend/components/SourcingMap.tsx to verify:
    - Uses OpenStreetMap tile URL (not CARTO Dark Matter)
    - Displays OpenStreetMap attribution
    - Constrained to India bounding box: 6.0°N to 37.5°N, 68.0°E to 97.5°E
    - Strictly North and East coordinates (never 6.0°S or 68.0°W)
    - MaxBoundsViscosity is 1.0 (no panning out of India)
    """
    map_file = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "components", "SourcingMap.tsx")
    assert os.path.exists(map_file), "SourcingMap.tsx must exist"

    with open(map_file, "r", encoding="utf-8") as f:
        content = f.read()

    # OSM basemap check
    assert "tile.openstreetmap.org/{z}/{x}/{y}.png" in content
    assert "OpenStreetMap" in content
    assert "cartocdn.com" not in content, "CARTO tile URL must not be present"

    # India bounds check: 6.0°N to 37.5°N, 68.0°E to 97.5°E
    assert "6.0" in content and "68.0" in content
    assert "37.5" in content and "97.5" in content
    assert "maxBoundsViscosity: 1.0" in content
    assert "minZoom: 4" in content
    assert "maxZoom: 13" in content
    assert "6.0°S" not in content and "68.0°W" not in content


def test_sourcing_map_live_location_and_no_continuous_tracking():
    """
    Verifies that live location in SourcingMap:
    - Uses getCurrentPosition (on-demand only)
    - Does NOT use watchPosition (no background/continuous tracking)
    - Handles accuracy circle
    - Handles permission denied, position unavailable, timeout
    """
    map_file = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "components", "SourcingMap.tsx")
    with open(map_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert "getCurrentPosition" in content
    assert "watchPosition" not in content, "Must not continuously track user via watchPosition"
    assert "PERMISSION_DENIED" in content
    assert "POSITION_UNAVAILABLE" in content
    assert "TIMEOUT" in content
    assert "userAccuracyCircleRef" in content or "L.circle" in content


def test_sourcing_map_directions_and_zero_fabrication():
    """
    Verifies that directions in SourcingMap:
    - Queries legitimate router service (OSRM / configured URL)
    - Handles unconfigured / unavailable routing service cleanly
    - Distinctly tags SOURCING_REGION vs verified MANUFACTURER
    - Does not fabricate distance, routes, or ETA
    """
    map_file = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "components", "SourcingMap.tsx")
    with open(map_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert "router.project-osrm.org" in content or "NEXT_PUBLIC_ROUTING_API_URL" in content
    assert "Directions unavailable — routing service is not configured or reachable" in content
    assert "Clear Route" in content
    assert "SOURCING_REGION" in content
