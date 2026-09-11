import os
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.firebase import initialize_firebase_admin, FIREBASE_ADMIN_AVAILABLE

try:
    from firebase_admin import firestore
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False


class FirestoreService:
    """
    Cloud Firestore Application Service.
    Manages user profiles, procurement requests, and lightweight activity audit logs.
    
    Security Guarantees:
    - Identity is derived strictly from verified Firebase UID (never client-supplied body).
    - Never stores passwords, secrets, Gemini keys, or database connection strings.
    - Operates with non-blocking graceful fallback in test/offline environments.
    """
    def __init__(self):
        self._db = None
        self._initialized = False

    def _get_client(self):
        if self._initialized:
            return self._db

        self._initialized = True
        if not FIREBASE_ADMIN_AVAILABLE or not FIRESTORE_AVAILABLE:
            logger.debug("[FIRESTORE] firebase-admin firestore package not available.")
            return None

        app = initialize_firebase_admin()
        if not app:
            logger.debug("[FIRESTORE] Firebase Admin app not available; Firestore client disabled.")
            return None

        try:
            self._db = firestore.client(app)
            logger.info(f"[FIRESTORE] Connected to Cloud Firestore for project '{settings.FIREBASE_PROJECT_ID}'")
            return self._db
        except Exception as e:
            logger.debug(f"[FIRESTORE] Firestore client initialization note: {e}")
            return None

    def sync_user_profile(
        self,
        firebase_uid: str,
        email: str,
        display_name: Optional[str] = None,
        organization_name: Optional[str] = None,
        role: str = "buyer",
        auth_provider: str = "password"
    ) -> bool:
        """
        Creates or updates users/{firebase_uid} in Cloud Firestore.
        Preserves user-managed organization and role on repeat logins.
        """
        if not firebase_uid or not firebase_uid.strip():
            return False

        clean_uid = firebase_uid.strip()
        clean_email = email.strip().lower()
        now_iso = datetime.now(timezone.utc).isoformat()

        db = self._get_client()
        if not db:
            return False

        try:
            doc_ref = db.collection("users").document(clean_uid)
            doc_snap = doc_ref.get()

            if not doc_snap.exists:
                doc_payload = {
                    "firebase_uid": clean_uid,
                    "email": clean_email,
                    "organization_name": (organization_name or "Enterprise Buyer").strip(),
                    "display_name": (display_name or clean_email.split("@")[0].title()).strip(),
                    "role": role.strip(),
                    "created_at": now_iso,
                    "updated_at": now_iso,
                    "auth_provider": auth_provider
                }
                doc_ref.set(doc_payload)
                logger.info(f"[FIRESTORE] Created user document in Firestore: users/{clean_uid}")
            else:
                existing = doc_snap.to_dict() or {}
                updates: Dict[str, Any] = {
                    "updated_at": now_iso,
                    "auth_provider": auth_provider
                }
                if display_name and display_name.strip() != existing.get("display_name"):
                    updates["display_name"] = display_name.strip()
                if organization_name and organization_name.strip() and existing.get("organization_name") == "Enterprise Buyer":
                    updates["organization_name"] = organization_name.strip()

                doc_ref.update(updates)
                logger.info(f"[FIRESTORE] Updated user document in Firestore: users/{clean_uid}")

            return True
        except Exception as e:
            logger.warning(f"[FIRESTORE] Note updating user profile in Firestore: {e}")
            return False

    def record_procurement_request(
        self,
        verified_firebase_uid: str,
        request_id: str,
        organization_name: str,
        requirements: Any,
        normalized_metadata: Optional[Dict[str, Any]] = None,
        status: str = "COMPLETED",
        items: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Records a procurement request and its items under:
        - procurement_requests/{request_id}
        - procurement_requests/{request_id}/items/{item_id}
        - user_activity/{activity_id}
        """
        if not verified_firebase_uid or not request_id:
            return False

        clean_uid = verified_firebase_uid.strip()
        now_iso = datetime.now(timezone.utc).isoformat()

        db = self._get_client()
        if not db:
            return False

        try:
            # 1. Main request document
            req_ref = db.collection("procurement_requests").document(request_id)
            req_payload = {
                "firebase_uid": clean_uid,
                "organization_name": organization_name.strip(),
                "procurement_requirements": requirements,
                "normalized_request_metadata": normalized_metadata or {},
                "status": status,
                "created_at": now_iso,
                "updated_at": now_iso
            }
            req_ref.set(req_payload)

            # 2. Subcollection items
            if items:
                items_coll = req_ref.collection("items")
                for item in items:
                    item_id = item.get("item_id") or f"item_{uuid.uuid4().hex[:8]}"
                    items_coll.document(item_id).set({
                        "item_id": item_id,
                        "product_type": item.get("product_type", "General Item"),
                        "specifications": item.get("specifications", {}),
                        "matched_standards": item.get("matched_standards", []),
                        "compliance_status": item.get("compliance_status", "UNKNOWN"),
                        "created_at": now_iso
                    })

            # 3. User activity log
            self.record_user_activity(
                verified_firebase_uid=clean_uid,
                action="PROCUREMENT_ANALYZED",
                request_id=request_id
            )

            logger.info(f"[FIRESTORE] Recorded procurement request '{request_id}' for user '{clean_uid}'")
            return True
        except Exception as e:
            logger.warning(f"[FIRESTORE] Error recording procurement request: {e}")
            return False

    def record_user_activity(
        self,
        verified_firebase_uid: str,
        action: str,
        request_id: Optional[str] = None
    ) -> bool:
        """
        Records an append-only activity log in user_activity/{activity_id}.
        """
        if not verified_firebase_uid:
            return False

        clean_uid = verified_firebase_uid.strip()
        now_iso = datetime.now(timezone.utc).isoformat()

        db = self._get_client()
        if not db:
            return False

        try:
            activity_id = f"act_{uuid.uuid4().hex}"
            db.collection("user_activity").document(activity_id).set({
                "activity_id": activity_id,
                "firebase_uid": clean_uid,
                "action": action.strip().toUpperCase() if hasattr(action, "toUpperCase") else action.strip().upper(),
                "request_id": request_id,
                "timestamp": now_iso
            })
            return True
        except Exception as e:
            logger.debug(f"[FIRESTORE] Note recording user activity: {e}")
            return False


# Singleton instance
firestore_service = FirestoreService()
