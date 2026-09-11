import base64
import json
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.repositories.user_repository import UserRepository
from backend.app.models.auth import UserSignUpRequest, UserSignInRequest

class AuthService:
    def __init__(self, user_repo: Optional[UserRepository] = None):
        self.user_repo = user_repo or UserRepository()
        self.secret_key = settings.AUTH_SECRET_KEY.encode("utf-8")

    @staticmethod
    def _b64url_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

    @staticmethod
    def _b64url_decode(s: str) -> bytes:
        rem = len(s) % 4
        if rem > 0:
            s += "=" * (4 - rem)
        return base64.urlsafe_b64decode(s.encode("utf-8"))

    def hash_password(self, password: str) -> str:
        salt = secrets.token_bytes(16)
        iterations = 100000
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return f"pbkdf2_sha256${iterations}${salt.hex()}${key.hex()}"

    def verify_password(self, password: str, password_hash: str) -> bool:
        try:
            parts = password_hash.split("$")
            if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
                return False
            iterations = int(parts[1])
            salt = bytes.fromhex(parts[2])
            expected_key = bytes.fromhex(parts[3])
            candidate_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
            return hmac.compare_digest(expected_key, candidate_key)
        except Exception as e:
            logger.error(f"Error during password verification: {e}")
            return False

    def create_token(self, user_id: str, email: str, remember_me: bool = False) -> str:
        duration_days = 30 if remember_me else settings.AUTH_TOKEN_EXPIRE_DAYS
        now = datetime.now(timezone.utc)
        exp = now + timedelta(days=duration_days)

        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": user_id,
            "email": email.strip().lower(),
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp())
        }

        header_b64 = self._b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        payload_b64 = self._b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        signature = hmac.new(self.secret_key, signing_input, hashlib.sha256).digest()
        sig_b64 = self._b64url_encode(signature)

        return f"{header_b64}.{payload_b64}.{sig_b64}"

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None
            header_b64, payload_b64, sig_b64 = parts
            signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
            expected_sig = hmac.new(self.secret_key, signing_input, hashlib.sha256).digest()
            candidate_sig = self._b64url_decode(sig_b64)
            if not hmac.compare_digest(expected_sig, candidate_sig):
                return None

            payload_bytes = self._b64url_decode(payload_b64)
            payload = json.loads(payload_bytes.decode("utf-8"))
            now_ts = int(datetime.now(timezone.utc).timestamp())
            if payload.get("exp", 0) < now_ts:
                return None

            return payload
        except Exception as e:
            logger.debug(f"Token verification failed: {e}")
            return None

    def signup_user(self, req: UserSignUpRequest) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[str]]:
        if req.password != req.confirm_password:
            return None, None, "Password and confirm password do not match"

        clean_email = req.email.strip().lower()
        existing = self.user_repo.get_user_by_email(clean_email)
        if existing:
            return None, None, "An account with this email address already exists"

        user_id = f"usr_{secrets.token_hex(8)}"
        hashed_password = self.hash_password(req.password)
        created = self.user_repo.create_user(
            user_id=user_id,
            name=req.name,
            email=clean_email,
            organization=req.organization,
            password_hash=hashed_password
        )
        if not created:
            return None, None, "Failed to create user account. Please try again."

        token = self.create_token(user_id=user_id, email=clean_email, remember_me=False)
        safe_user = {k: v for k, v in created.items() if k != "password_hash"}
        return safe_user, token, None

    def signin_user(self, req: UserSignInRequest) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[str]]:
        clean_email = req.email.strip().lower()
        user = self.user_repo.get_user_by_email(clean_email)
        if not user:
            return None, None, "Invalid email or password"

        if not self.verify_password(req.password, user.get("password_hash", "")):
            return None, None, "Invalid email or password"

        token = self.create_token(
            user_id=user["id"],
            email=clean_email,
            remember_me=bool(req.remember_me)
        )
        safe_user = {k: v for k, v in user.items() if k != "password_hash"}
        return safe_user, token, None

    def get_current_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        # 1. First attempt verification as a cryptographically signed Firebase ID token
        try:
            from backend.app.core.firebase import verify_firebase_id_token
            fb_decoded = verify_firebase_id_token(token)
            if fb_decoded and "uid" in fb_decoded:
                fb_uid = fb_decoded["uid"]
                user = self.user_repo.get_user_by_firebase_uid(fb_uid)
                if not user:
                    fb_email = fb_decoded.get("email") or f"{fb_uid}@firebase.user"
                    fb_name = fb_decoded.get("name")
                    user = self.user_repo.upsert_firebase_user(
                        firebase_uid=fb_uid,
                        email=fb_email,
                        name=fb_name
                    )
                if user:
                    return {k: v for k, v in user.items() if k != "password_hash"}
        except Exception as e:
            logger.debug(f"[AUTH] Firebase token evaluation note: {e}")

        # 2. Fallback to local HMAC-signed JWT token (only if ENABLE_LEGACY_AUTH is True)
        if not settings.ENABLE_LEGACY_AUTH:
            logger.debug("[AUTH] Legacy HMAC token ignored (ENABLE_LEGACY_AUTH=False)")
            return None

        payload = self.verify_token(token)
        if not payload:
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            return None
        return {k: v for k, v in user.items() if k != "password_hash"}

    def sync_firebase_user(
        self,
        token: str,
        name: Optional[str] = None,
        organization: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        from backend.app.core.firebase import verify_firebase_id_token
        fb_decoded = verify_firebase_id_token(token)
        if not fb_decoded or "uid" not in fb_decoded:
            return None, "Invalid or expired Firebase authentication token"

        fb_uid = fb_decoded["uid"]
        fb_email = fb_decoded.get("email") or f"{fb_uid}@firebase.user"
        effective_name = name or fb_decoded.get("name")
        
        # Identify auth provider ('google' or 'password')
        raw_provider = fb_decoded.get("firebase", {}).get("sign_in_provider", "password")
        auth_provider = "google" if "google" in raw_provider else "password"

        user = self.user_repo.upsert_firebase_user(
            firebase_uid=fb_uid,
            email=fb_email,
            name=effective_name,
            organization=organization
        )
        if not user:
            return None, "Failed to synchronize user account"

        # Synchronize user profile with Cloud Firestore
        try:
            from backend.app.services.firestore_service import firestore_service
            firestore_service.sync_user_profile(
                firebase_uid=fb_uid,
                email=fb_email,
                display_name=effective_name or user.get("name"),
                organization_name=organization or user.get("organization"),
                auth_provider=auth_provider
            )
        except Exception as e:
            logger.debug(f"[AUTH] Background Firestore user sync note: {e}")

        safe_user = {k: v for k, v in user.items() if k != "password_hash"}
        return safe_user, None
