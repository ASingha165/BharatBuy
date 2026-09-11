import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.api.dependencies import get_user_repository, get_auth_service
from backend.app.core.firebase import verify_firebase_id_token

TEST_FB_UID = "fb_test_uid_998877"
TEST_FB_EMAIL = "fb.verified.user@bharatprocure.gov.in"
TEST_MOCK_TOKEN = f"test_mock_token:{TEST_FB_UID}:{TEST_FB_EMAIL}"

@pytest.fixture
def client():
    """Returns a fresh isolated TestClient per test without cookie bleed."""
    return TestClient(app)

@pytest.fixture(autouse=True)
def clean_firebase_test_user():
    user_repo = get_user_repository()
    # Clean up test accounts before and after tests
    user_repo.delete_users_by_emails([TEST_FB_EMAIL, "link.test@domain.in", f"{TEST_FB_EMAIL}_tampered_signature"])
    user_repo.delete_user_by_firebase_uid(TEST_FB_UID)
    user_repo.delete_user_by_firebase_uid("fb_linked_uid_999")
    yield
    user_repo.delete_users_by_emails([TEST_FB_EMAIL, "link.test@domain.in", f"{TEST_FB_EMAIL}_tampered_signature"])
    user_repo.delete_user_by_firebase_uid(TEST_FB_UID)
    user_repo.delete_user_by_firebase_uid("fb_linked_uid_999")


def test_verify_firebase_token_helper():
    # Empty token returns None
    assert verify_firebase_id_token("") is None
    assert verify_firebase_id_token("   ") is None

    # Test mock token decoding
    decoded = verify_firebase_id_token(TEST_MOCK_TOKEN)
    assert decoded is not None
    assert decoded["uid"] == TEST_FB_UID
    assert decoded["email"] == TEST_FB_EMAIL
    assert decoded.get("email_verified") is True


def test_firebase_sync_endpoint_success(client):
    payload = {
        "name": "Priya Sundaram",
        "organization": "Tamil Nadu Clean Energy Agency"
    }
    response = client.post(
        "/api/v1/auth/firebase-sync",
        json=payload,
        headers={"Authorization": f"Bearer {TEST_MOCK_TOKEN}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "user" in data
    assert data["user"]["email"] == TEST_FB_EMAIL
    assert data["user"]["name"] == "Priya Sundaram"
    assert data["user"]["organization"] == "Tamil Nadu Clean Energy Agency"
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]

    # Cookie check
    cookie = response.cookies.get("bharatbuy_session")
    assert cookie is not None


def test_firebase_sync_missing_token_returns_401(client):
    payload = {
        "name": "Unauthorized User",
        "organization": "No Auth"
    }
    response = client.post(
        "/api/v1/auth/firebase-sync",
        json=payload
    )
    assert response.status_code == 401
    assert "required" in response.json()["detail"].lower()


def test_firebase_sync_invalid_token_returns_401(client):
    payload = {
        "name": "Invalid User",
        "organization": "Bad Auth"
    }
    response = client.post(
        "/api/v1/auth/firebase-sync",
        json=payload,
        headers={"Authorization": "Bearer invalid_garbage_token_12345"}
    )
    assert response.status_code == 401


def test_authenticated_get_me_with_firebase_token(client):
    # First sync user
    client.post(
        "/api/v1/auth/firebase-sync",
        json={"name": "Priya Sundaram", "organization": "Tamil Nadu Clean Energy Agency"},
        headers={"Authorization": f"Bearer {TEST_MOCK_TOKEN}"}
    )

    # Calling /me with the Bearer Firebase token
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {TEST_MOCK_TOKEN}"}
    )
    assert response.status_code == 200
    user = response.json()
    assert user["email"] == TEST_FB_EMAIL
    assert user["name"] == "Priya Sundaram"


def test_firebase_upsert_account_linking(client):
    user_repo = get_user_repository()
    auth_svc = get_auth_service()

    # Pre-create a local user by email
    local_user = user_repo.create_user(
        user_id="usr_precreated_123",
        name="Existing Account",
        email="link.test@domain.in",
        organization="Existing Org Ltd",
        password_hash=auth_svc.hash_password("Password123!")
    )
    assert local_user is not None

    # Now upsert with a Firebase UID for the same email
    fb_link_token = "test_mock_token:fb_linked_uid_999:link.test@domain.in"
    response = client.post(
        "/api/v1/auth/firebase-sync",
        json={"name": "Existing Account Updated"},
        headers={"Authorization": f"Bearer {fb_link_token}"}
    )
    assert response.status_code == 200
    synced = response.json()["user"]
    # Account should be linked to the same ID without creating a duplicate
    assert synced["id"] == "usr_precreated_123"
    assert synced["email"] == "link.test@domain.in"


def test_unauthenticated_get_me_returns_401(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert "Authentication required" in response.json()["detail"]


def test_client_cannot_spoof_firebase_uid_or_email(client):
    # Attacker attempts to send spoofed UID and email in JSON request body
    malicious_payload = {
        "uid": "attacker_fake_root_uid_99999",
        "email": "root.admin@gov.in",
        "name": "Priya Sundaram",
        "organization": "State Energy Dept"
    }
    response = client.post(
        "/api/v1/auth/firebase-sync",
        json=malicious_payload,
        headers={"Authorization": f"Bearer {TEST_MOCK_TOKEN}"}
    )
    assert response.status_code == 200
    synced_user = response.json()["user"]

    # Security Assertion: The registered email MUST be the one from the cryptographically verified token
    assert synced_user["email"] == TEST_FB_EMAIL
    assert synced_user["email"] != "root.admin@gov.in"
    assert synced_user["name"] == "Priya Sundaram"


def test_expired_or_forged_firebase_token_rejected(client):
    # 1. Tampered token signature
    tampered_token = f"{TEST_MOCK_TOKEN}_tampered_signature"
    res_tampered = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tampered_token}"}
    )
    # Tampered token fails verification and must return 401
    assert res_tampered.status_code == 401

    # 2. Empty / whitespace bearer token
    res_empty = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer   "}
    )
    assert res_empty.status_code == 401

    # 3. Forged JWT without matching key/issuer
    fake_jwt = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOiJmYWtlX3VpZCIsImV4cCI6MTU3NzgzNjgwMH0.fakesig"
    res_fake = client.post(
        "/api/v1/auth/firebase-sync",
        json={"name": "Hacker"},
        headers={"Authorization": f"Bearer {fake_jwt}"}
    )
    assert res_fake.status_code == 401

