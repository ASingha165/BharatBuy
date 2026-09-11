import urllib.request
import urllib.error
import json
import re
import os
import sys
import socket
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def _frontend_running() -> bool:
    """Return True only if Next.js dev server is reachable on localhost:3000."""
    try:
        with socket.create_connection(("localhost", 3000), timeout=1):
            return True
    except OSError:
        return False


_FRONTEND_UP = _frontend_running()


def _verify_page(url_path, expected_title, expected_fields):
    url = f"http://localhost:3000{url_path}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200, f"Expected 200, got {resp.status}"
        html = resp.read().decode('utf-8')
    
    assert expected_title in html, f"Missing title '{expected_title}'"
    for field in expected_fields:
        assert field in html, f"Missing field '{field}' in {url_path}"
    
    # Check that inputs do not have hardcoded values
    inputs = re.findall(r'<input[^>]+>', html)
    for inp in inputs:
        val_match = re.search(r'value="([^"]+)"', inp)
        if val_match:
            val = val_match.group(1)
            assert "@" not in val, f"Hardcoded email found in input: {inp}"
            assert val != "password", f"Hardcoded password found in input: {inp}"

@pytest.mark.skipif(not _FRONTEND_UP, reason="Next.js dev server not running on localhost:3000")
def test_signin_route_signed_out():
    """Verify /signin renders HTTP 200 with blank form fields while signed out."""
    _verify_page("/signin", "Sign in to BharatBuy", ["signin-email", "signin-password"])

@pytest.mark.skipif(not _FRONTEND_UP, reason="Next.js dev server not running on localhost:3000")
def test_signup_route_signed_out():
    """Verify /signup renders HTTP 200 with blank form fields while signed out."""
    _verify_page("/signup", "Create BharatBuy Account", [
        "signup-name", "signup-email", "signup-organization",
        "signup-password", "signup-confirm-password", "signup-terms"
    ])

@pytest.mark.skipif(not _FRONTEND_UP, reason="Next.js dev server not running on localhost:3000")
def test_home_route():
    """Verify / renders HTTP 200 cleanly."""
    _verify_page("/", "BharatBuy", [])

def test_protected_endpoint_missing_token_returns_401():
    """Verify protected /api/v1/auth/me returns 401 when called without Authorization token."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401

def test_protected_endpoint_invalid_token_returns_401():
    """Verify protected /api/v1/auth/me returns 401 when called with forged/invalid token."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.fake.token"}
    )
    assert response.status_code == 401

def test_protected_endpoint_valid_firebase_token_succeeds():
    """Verify protected /api/v1/auth/me succeeds with valid Firebase token."""
    uid = "usr_test_regress_401"
    email = "verified_buyer@enterprise.in"
    token = f"test_mock_token:{uid}:{email}"

    # First sync user
    sync_resp = client.post(
        "/api/v1/auth/firebase-sync",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Verified Enterprise Buyer", "organization": "Bharat Procurement Corp"}
    )
    assert sync_resp.status_code == 200

    # Then access /auth/me
    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_resp.status_code == 200
    data = me_resp.json()
    assert data["email"] == email

def test_signed_out_auth_context_code_audit():
    """Verify frontend/lib/auth-context.tsx has zero calls to protected APIs when signed out."""
    auth_ctx_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "lib", "auth-context.tsx")
    with open(auth_ctx_path, "r", encoding="utf-8") as f:
        content = f.read()

    # onAuthStateChanged signed out block must not call getCurrentUserApi
    signed_out_block = re.search(r'else\s*\{[^}]*setAuthState\(\'SIGNED_OUT\'\)[^}]*\}', content, re.DOTALL)
    assert signed_out_block is not None, "Signed-out block not found"
    assert "getCurrentUserApi" not in signed_out_block.group(0), "Signed-out block must not call getCurrentUserApi!"
    assert "refreshUser" not in signed_out_block.group(0), "Signed-out block must not call refreshUser!"

if __name__ == "__main__":
    test_signin_route_signed_out()
    test_signup_route_signed_out()
    test_home_route()
    test_protected_endpoint_missing_token_returns_401()
    test_protected_endpoint_invalid_token_returns_401()
    test_protected_endpoint_valid_firebase_token_succeeds()
    test_signed_out_auth_context_code_audit()
    print("ALL REGRESSION CHECKS PASSED!")
