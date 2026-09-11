import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.api.dependencies import get_auth_service, get_user_repository
from backend.app.core.config import settings

client = TestClient(app)

@pytest.fixture(autouse=True)
def enable_legacy_auth_fixture():
    original = settings.ENABLE_LEGACY_AUTH
    settings.ENABLE_LEGACY_AUTH = True
    yield
    settings.ENABLE_LEGACY_AUTH = original

@pytest.fixture(autouse=True)
def clean_test_users():
    user_repo = get_user_repository()
    # Clean up test accounts before and after tests
    test_emails = [
        "procurement.lead@bharat-infra.in",
        "duplicate.user@domain.in",
        "session.test@domain.in",
        "bearer.test@domain.in",
        "cookie.test@domain.in",
        "signout.test@domain.in"
    ]
    for email in test_emails:
        user_repo.delete_user_by_email(email)
    yield
    user_repo.delete_users_by_emails(test_emails)


def test_signup_success():
    payload = {
        "name": "Arjun Sharma",
        "email": "procurement.lead@bharat-infra.in",
        "organization": "Bharat Infra Projects Ltd",
        "password": "SecurePassword2026!",
        "confirm_password": "SecurePassword2026!",
        "terms_accepted": True
    }
    response = client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "user" in data
    assert "token" in data
    assert data["user"]["email"] == "procurement.lead@bharat-infra.in"
    assert data["user"]["name"] == "Arjun Sharma"
    assert data["user"]["organization"] == "Bharat Infra Projects Ltd"
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]

    # Cookie check
    cookie = response.cookies.get("bharatbuy_session")
    assert cookie is not None
    assert len(cookie) > 20


def test_signup_duplicate_email():
    payload = {
        "name": "Dev User",
        "email": "duplicate.user@domain.in",
        "organization": "Testing Corp",
        "password": "StrongPassword1!",
        "confirm_password": "StrongPassword1!",
        "terms_accepted": True
    }
    # First signup should succeed
    res1 = client.post("/api/v1/auth/signup", json=payload)
    assert res1.status_code == 201

    # Second signup with same email must fail with 400
    res2 = client.post("/api/v1/auth/signup", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"].lower()


def test_signup_validation_errors():
    base_payload = {
        "name": "Test User",
        "email": "invalid-email-format",
        "organization": "Testing Corp",
        "password": "Short1!",
        "confirm_password": "Short1!",
        "terms_accepted": True
    }

    # Invalid email
    res = client.post("/api/v1/auth/signup", json=base_payload)
    assert res.status_code == 422

    # Password mismatch
    payload_mismatch = {
        "name": "Test User",
        "email": "valid.user@domain.in",
        "organization": "Testing Corp",
        "password": "ValidPassword123!",
        "confirm_password": "DifferentPassword123!",
        "terms_accepted": True
    }
    res_mismatch = client.post("/api/v1/auth/signup", json=payload_mismatch)
    assert res_mismatch.status_code == 400
    assert "match" in res_mismatch.json()["detail"].lower()

    # Terms not accepted
    payload_no_terms = {
        "name": "Test User",
        "email": "valid.user@domain.in",
        "organization": "Testing Corp",
        "password": "ValidPassword123!",
        "confirm_password": "ValidPassword123!",
        "terms_accepted": False
    }
    res_terms = client.post("/api/v1/auth/signup", json=payload_no_terms)
    assert res_terms.status_code == 422


def test_password_hashing_and_security():
    auth_svc = get_auth_service()
    raw_password = "SuperSecretPassword123!"
    hash1 = auth_svc.hash_password(raw_password)
    hash2 = auth_svc.hash_password(raw_password)

    # Different salts must produce distinct hashes
    assert hash1 != hash2
    assert hash1.startswith("pbkdf2_sha256$100000$")
    assert raw_password not in hash1

    # Verification must succeed for correct password and fail for wrong password
    assert auth_svc.verify_password(raw_password, hash1) is True
    assert auth_svc.verify_password("WrongPassword123!", hash1) is False
    assert auth_svc.verify_password(raw_password, "invalid_hash_format") is False


def test_signin_success_and_cookie():
    signup_payload = {
        "name": "Cookie Tester",
        "email": "cookie.test@domain.in",
        "organization": "Cookie Infra",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "terms_accepted": True
    }
    res_signup = client.post("/api/v1/auth/signup", json=signup_payload)
    assert res_signup.status_code == 201

    signin_payload = {
        "email": "cookie.test@domain.in",
        "password": "SecurePassword123!",
        "remember_me": True
    }
    response = client.post("/api/v1/auth/signin", json=signin_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "cookie.test@domain.in"
    assert "password_hash" not in data["user"]
    assert response.cookies.get("bharatbuy_session") is not None


def test_signin_wrong_password_and_nonexistent_user():
    # Nonexistent user
    res_nonexistent = client.post("/api/v1/auth/signin", json={
        "email": "nonexistent.user@unknown.in",
        "password": "AnyPassword123!"
    })
    assert res_nonexistent.status_code == 401
    assert "invalid email or password" in res_nonexistent.json()["detail"].lower()

    # Create user first
    client.post("/api/v1/auth/signup", json={
        "name": "Session Tester",
        "email": "session.test@domain.in",
        "organization": "Session Corp",
        "password": "CorrectPassword123!",
        "confirm_password": "CorrectPassword123!",
        "terms_accepted": True
    })

    # Wrong password
    res_wrong = client.post("/api/v1/auth/signin", json={
        "email": "session.test@domain.in",
        "password": "IncorrectPassword123!"
    })
    assert res_wrong.status_code == 401
    assert "invalid email or password" in res_wrong.json()["detail"].lower()


def test_me_endpoint_authenticated_via_bearer_and_cookie():
    signup_payload = {
        "name": "Bearer Tester",
        "email": "bearer.test@domain.in",
        "organization": "Bearer Org",
        "password": "BearerPassword123!",
        "confirm_password": "BearerPassword123!",
        "terms_accepted": True
    }
    res_signup = client.post("/api/v1/auth/signup", json=signup_payload)
    assert res_signup.status_code == 201
    token = res_signup.json()["token"]

    # 1. Access /me via Bearer token
    res_me_bearer = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_me_bearer.status_code == 200
    me_data = res_me_bearer.json()
    assert me_data["email"] == "bearer.test@domain.in"
    assert me_data["name"] == "Bearer Tester"
    assert "password_hash" not in me_data

    # 2. Access /me via cookie
    client.cookies.set("bharatbuy_session", token)
    res_me_cookie = client.get("/api/v1/auth/me")
    assert res_me_cookie.status_code == 200
    assert res_me_cookie.json()["email"] == "bearer.test@domain.in"
    client.cookies.clear()


def test_me_unauthenticated_returns_401():
    # Without cookie or token
    client.cookies.clear()
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert "authentication required" in res.json()["detail"].lower()

    # With invalid token
    res_invalid = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.malformed.token"}
    )
    assert res_invalid.status_code == 401


def test_signout_clears_session():
    signup_payload = {
        "name": "Signout Tester",
        "email": "signout.test@domain.in",
        "organization": "Signout Corp",
        "password": "SignoutPassword123!",
        "confirm_password": "SignoutPassword123!",
        "terms_accepted": True
    }
    client.post("/api/v1/auth/signup", json=signup_payload)

    # Signout endpoint
    res_signout = client.post("/api/v1/auth/signout")
    assert res_signout.status_code == 200
    assert "sign out successful" in res_signout.json()["message"].lower()


def test_legacy_auth_disabled_rejection():
    # Explicitly disable legacy auth
    settings.ENABLE_LEGACY_AUTH = False
    try:
        # Signup attempt should return 403 Forbidden
        signup_res = client.post("/api/v1/auth/signup", json={
            "name": "Blocked User",
            "email": "blocked@domain.in",
            "organization": "Blocked Corp",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "terms_accepted": True
        })
        assert signup_res.status_code == 403
        assert "disabled" in signup_res.json()["detail"].lower()

        # Signin attempt should return 403 Forbidden
        signin_res = client.post("/api/v1/auth/signin", json={
            "email": "blocked@domain.in",
            "password": "Password123!"
        })
        assert signin_res.status_code == 403
        assert "disabled" in signin_res.json()["detail"].lower()
    finally:
        settings.ENABLE_LEGACY_AUTH = True


def test_legacy_token_rejected_when_disabled():
    # Generate a legacy token with auth enabled
    auth_svc = get_auth_service()
    legacy_token = auth_svc.create_token("usr_test123", "test@domain.in")

    # Now disable legacy auth
    settings.ENABLE_LEGACY_AUTH = False
    try:
        # Resolving user from token should return None
        resolved = auth_svc.get_current_user_from_token(legacy_token)
        assert resolved is None

        # Accessing /me with the legacy token should return 401 Unauthorized
        res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {legacy_token}"})
        assert res.status_code == 401
    finally:
        settings.ENABLE_LEGACY_AUTH = True

