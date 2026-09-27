import os
import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.database import DatabaseManager, db_manager, PSYCOPG2_AVAILABLE

if PSYCOPG2_AVAILABLE:
    import psycopg2
    IntegrityErrors = (sqlite3.IntegrityError, psycopg2.IntegrityError)
else:
    IntegrityErrors = (sqlite3.IntegrityError,)


class ProductionPersistenceError(RuntimeError):
    """
    Raised when history persistence is requested in a production environment (e.g. Vercel)
    without configured durable storage (Cloud Firestore or PostgreSQL/Neon).
    Local SQLite is strictly prohibited for production history persistence.
    """
    pass


class ProcurementHistoryRepository:
    """
    Procurement History Data Access Layer.
    Persists and retrieves user-owned procurement analysis snapshots.
    
    Persistence Policy:
    1. PRODUCTION:
       - Must use durable external storage:
         * Primary A: Cloud Firestore (users/{firebase_uid}/procurement_history/{id})
         * Primary B: Neon / Cloud PostgreSQL (procurement_history table via DATABASE_URL)
       - Local SQLite is strictly prohibited in production (never writes or falls back silently to SQLite on Vercel).
       - If neither durable store is configured in production, operations raise ProductionPersistenceError.
    
    2. LOCAL DEVELOPMENT & TESTING:
       - Cloud Firestore may be used if configured.
       - PostgreSQL may be used if DATABASE_URL is configured.
       - Local SQLite fallback is permitted for offline development and deterministic unit testing.
    
    Guarantees:
    - User isolation: every record is strictly bound to the authenticated user ID / Firebase UID.
    - Zero secrets/tokens stored.
    """
    def __init__(self, db_path: Optional[str] = None, manager: Optional[DatabaseManager] = None):
        if manager:
            self.manager = manager
        elif db_path:
            self.manager = DatabaseManager(sqlite_path=db_path)
        else:
            self.manager = db_manager
        self._init_db()

    @property
    def engine_name(self) -> str:
        return self.manager.engine_name

    def is_production(self) -> bool:
        """Determines whether the application is running in a production environment."""
        return settings.is_production

    def has_firestore(self) -> bool:
        """Checks whether Cloud Firestore client is active and reachable."""
        try:
            from backend.app.services.firestore_service import firestore_service
            client = firestore_service._get_client()
            return client is not None
        except Exception:
            return False

    def is_durable_storage_available(self) -> bool:
        """Returns True if at least one durable external persistence engine is configured."""
        return self.manager.is_postgres or self.has_firestore()

    def get_connection(self):
        return self.manager.get_connection()

    def _init_db(self) -> None:
        """
        Initializes the relational procurement_history table if relational storage is active.
        In production without PostgreSQL, skips SQLite table creation completely.
        """
        if self.manager.is_postgres:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS procurement_history (
                        procurement_id VARCHAR(128) PRIMARY KEY,
                        user_id VARCHAR(128) NOT NULL,
                        firebase_uid VARCHAR(128),
                        company_name VARCHAR(255) NOT NULL,
                        request_status VARCHAR(64) NOT NULL DEFAULT 'COMPLETED',
                        snapshot_json TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_proc_hist_user_id ON procurement_history(user_id);
                    CREATE INDEX IF NOT EXISTS idx_proc_hist_fb_uid ON procurement_history(firebase_uid);
                    CREATE INDEX IF NOT EXISTS idx_proc_hist_created ON procurement_history(created_at DESC);
                    """)
                    conn.commit()
                logger.info("[POSTGRESQL] Initialized procurement_history table in durable PostgreSQL")
            except Exception as e:
                logger.error(f"[POSTGRESQL] Failed to initialize procurement_history table: {e}")
            return

        if self.is_production():
            logger.info(
                "[HISTORY] Production environment active without PostgreSQL. "
                "Local SQLite history table initialization skipped; durable history persistence is assigned to Cloud Firestore."
            )
            return

        # Local development / testing mode with SQLite
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS procurement_history (
                    procurement_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    firebase_uid TEXT,
                    company_name TEXT NOT NULL,
                    request_status TEXT NOT NULL DEFAULT 'COMPLETED',
                    snapshot_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_proc_hist_user_id ON procurement_history(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_proc_hist_fb_uid ON procurement_history(firebase_uid)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_proc_hist_created ON procurement_history(created_at DESC)")
                conn.commit()
            logger.info("[SQLITE] Initialized local development procurement_history table")
        except Exception as e:
            logger.error(f"[SQLITE] Failed to initialize development procurement_history table: {e}")

    def save_snapshot(
        self,
        user_id: str,
        firebase_uid: Optional[str],
        record: Dict[str, Any]
    ) -> bool:
        """
        Saves a procurement analysis snapshot for the authenticated user.
        Strict production policy:
        - If production: requires durable storage (Cloud Firestore or PostgreSQL/Neon).
          Never silently writes or falls back to local SQLite on Vercel/production.
        - If development: uses Firestore if configured, PostgreSQL if configured, or local SQLite fallback.
        """
        if not user_id or not record.get("procurement_id"):
            return False

        # Production safety enforcement: strictly fail if no durable store configured
        if self.is_production() and not self.is_durable_storage_available():
            err_msg = (
                "Production environment requires durable persistence (Cloud Firestore or PostgreSQL/Neon). "
                "Local SQLite persistence is strictly prohibited in production."
            )
            logger.error(f"[PERSISTENCE GATE] {err_msg}")
            raise ProductionPersistenceError(err_msg)

        procurement_id = str(record["procurement_id"]).strip()
        company_name = str(record.get("company_name", "Enterprise Buyer")).strip()
        request_status = str(record.get("request_status", "COMPLETED")).strip()
        now_iso = datetime.now(timezone.utc).isoformat()
        created_at = record.get("analysis_created_at") or now_iso
        target_uid = firebase_uid or user_id

        # Clean copy for serialization without credentials, session keys, or sensitive secrets
        clean_snapshot = {
            "procurement_id": procurement_id,
            "uid": target_uid,
            "company_name": company_name,
            "analysis_created_at": created_at,
            "updated_at": now_iso,
            "request_status": request_status,
            "ai_provider": record.get("ai_provider", "deterministic_fallback"),
            "request": record.get("request", {}),
            "items": record.get("items", []),
            "budget": record.get("budget", {}),
            "location": record.get("location", {}),
            "search": record.get("search", {}),
            "sourcing": record.get("sourcing", {}),
            "analysis": record.get("analysis", {})
        }

        # 1. Cloud Firestore Durable Storage (Primary store if configured)
        if self.has_firestore():
            try:
                from backend.app.services.firestore_service import firestore_service
                db = firestore_service._get_client()
                if db:
                    db.collection("users").document(target_uid).collection("procurement_history").document(procurement_id).set(clean_snapshot)
                    logger.info(f"[FIRESTORE] Saved procurement history '{procurement_id}' to Cloud Firestore")

                    # If PostgreSQL is also active, mirror for relational analytics
                    if self.manager.is_postgres:
                        try:
                            snapshot_str = json.dumps(clean_snapshot, default=str)
                            with self.get_connection() as conn:
                                cursor = conn.cursor()
                                cursor.execute("""
                                INSERT INTO procurement_history (
                                    procurement_id, user_id, firebase_uid, company_name,
                                    request_status, snapshot_json, created_at, updated_at
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (procurement_id) DO UPDATE SET
                                    company_name = EXCLUDED.company_name,
                                    request_status = EXCLUDED.request_status,
                                    snapshot_json = EXCLUDED.snapshot_json,
                                    updated_at = EXCLUDED.updated_at
                                """, (procurement_id, user_id, firebase_uid, company_name, request_status, snapshot_str, created_at, now_iso))
                                conn.commit()
                            logger.info(f"[POSTGRESQL] Mirrored history snapshot '{procurement_id}' to PostgreSQL")
                        except Exception as pg_mirror_err:
                            logger.debug(f"[POSTGRESQL] Mirror note: {pg_mirror_err}")

                    return True
            except Exception as fs_err:
                logger.error(f"[FIRESTORE] Error saving procurement history: {fs_err}")
                if self.is_production():
                    raise ProductionPersistenceError(f"Cloud Firestore history persistence failed in production: {fs_err}") from fs_err
                # In development, fall through to SQLite fallback

        # 2. PostgreSQL Durable Storage (Secondary durable store if Firestore not active)
        if self.manager.is_postgres:
            try:
                snapshot_str = json.dumps(clean_snapshot, default=str)
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                    INSERT INTO procurement_history (
                        procurement_id, user_id, firebase_uid, company_name,
                        request_status, snapshot_json, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (procurement_id) DO UPDATE SET
                        company_name = EXCLUDED.company_name,
                        request_status = EXCLUDED.request_status,
                        snapshot_json = EXCLUDED.snapshot_json,
                        updated_at = EXCLUDED.updated_at
                    """, (procurement_id, user_id, firebase_uid, company_name, request_status, snapshot_str, created_at, now_iso))
                    conn.commit()
                logger.info(f"[POSTGRESQL] Saved procurement history '{procurement_id}' to PostgreSQL for user '{user_id}'")
                return True
            except Exception as e:
                logger.error(f"[POSTGRESQL] Error saving procurement history: {e}")
                if self.is_production():
                    raise ProductionPersistenceError(f"PostgreSQL history persistence failed in production: {e}") from e
                return False

        # 3. Local Development SQLite Fallback
        # STRICTLY PROHIBITED in production
        if self.is_production():
            err_msg = (
                "Production environment requires durable persistence (Cloud Firestore or PostgreSQL/Neon). "
                "Local SQLite persistence is strictly prohibited in production."
            )
            logger.error(f"[PERSISTENCE GATE] {err_msg}")
            raise ProductionPersistenceError(err_msg)

        try:
            snapshot_str = json.dumps(clean_snapshot, default=str)
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO procurement_history (
                    procurement_id, user_id, firebase_uid, company_name,
                    request_status, snapshot_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(procurement_id) DO UPDATE SET
                    company_name = excluded.company_name,
                    request_status = excluded.request_status,
                    snapshot_json = excluded.snapshot_json,
                    updated_at = excluded.updated_at
                """, (procurement_id, user_id, firebase_uid, company_name, request_status, snapshot_str, created_at, now_iso))
                conn.commit()
            logger.info(f"[SQLITE] Saved development procurement history '{procurement_id}' for user '{user_id}'")
            return True
        except Exception as e:
            logger.error(f"[SQLITE] Error saving development history snapshot: {e}")
            return False

    def list_snapshots(
        self,
        user_id: str,
        firebase_uid: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves all procurement history records belonging to the authenticated user.
        Strict user isolation: only returns records matching user_id or firebase_uid.
        """
        if not user_id:
            return []

        if self.is_production() and not self.is_durable_storage_available():
            err_msg = (
                "Production environment requires durable persistence (Cloud Firestore or PostgreSQL/Neon). "
                "Local SQLite persistence is strictly prohibited in production."
            )
            logger.error(f"[PERSISTENCE GATE] {err_msg}")
            raise ProductionPersistenceError(err_msg)

        target_uid = firebase_uid or user_id

        # 1. Cloud Firestore (Primary durable store)
        if self.has_firestore():
            try:
                from backend.app.services.firestore_service import firestore_service
                from firebase_admin import firestore
                db = firestore_service._get_client()
                if db:
                    docs = (
                        db.collection("users")
                        .document(target_uid)
                        .collection("procurement_history")
                        .order_by("analysis_created_at", direction=firestore.Query.DESCENDING)
                        .stream()
                    )
                    results = []
                    for doc in docs:
                        data = doc.to_dict()
                        if data:
                            results.append(data)
                    return results
            except Exception as fs_err:
                logger.error(f"[FIRESTORE] Error listing history: {fs_err}")
                if self.is_production():
                    raise ProductionPersistenceError(f"Cloud Firestore history retrieval failed in production: {fs_err}") from fs_err

        # 2. PostgreSQL (Secondary durable store)
        if self.manager.is_postgres:
            try:
                query = """
                SELECT procurement_id, company_name, request_status, snapshot_json, created_at, updated_at
                FROM procurement_history
                WHERE user_id = %s OR firebase_uid = %s
                ORDER BY created_at DESC
                """
                rows = self.manager.fetch_all(query, (user_id, target_uid))
                results = []
                for row in rows:
                    try:
                        results.append(json.loads(row["snapshot_json"]))
                    except Exception:
                        pass
                return results
            except Exception as e:
                logger.error(f"[POSTGRESQL] Error listing history: {e}")
                if self.is_production():
                    raise ProductionPersistenceError(f"PostgreSQL history retrieval failed in production: {e}") from e
                return []

        # 3. Local Development SQLite Fallback
        # STRICTLY PROHIBITED in production
        if self.is_production():
            raise ProductionPersistenceError(
                "Production environment requires durable persistence (Cloud Firestore or PostgreSQL/Neon). "
                "Local SQLite persistence is strictly prohibited in production."
            )

        try:
            query = """
            SELECT procurement_id, company_name, request_status, snapshot_json, created_at, updated_at
            FROM procurement_history
            WHERE user_id = ? OR firebase_uid = ?
            ORDER BY created_at DESC
            """
            rows = self.manager.fetch_all(query, (user_id, target_uid))
            results = []
            for row in rows:
                try:
                    results.append(json.loads(row["snapshot_json"]))
                except Exception:
                    pass
            return results
        except Exception as e:
            logger.error(f"[SQLITE] Error listing development history: {e}")
            return []

    def get_snapshot(
        self,
        procurement_id: str,
        user_id: str,
        firebase_uid: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single procurement history snapshot if owned by the user.
        """
        if not procurement_id or not user_id:
            return None

        if self.is_production() and not self.is_durable_storage_available():
            raise ProductionPersistenceError(
                "Production environment requires durable persistence (Cloud Firestore or PostgreSQL/Neon). "
                "Local SQLite persistence is strictly prohibited in production."
            )

        target_uid = firebase_uid or user_id

        # 1. Cloud Firestore
        if self.has_firestore():
            try:
                from backend.app.services.firestore_service import firestore_service
                db = firestore_service._get_client()
                if db:
                    doc = db.collection("users").document(target_uid).collection("procurement_history").document(procurement_id).get()
                    if doc.exists:
                        return doc.to_dict()
                return None
            except Exception as fs_err:
                logger.error(f"[FIRESTORE] Error fetching history '{procurement_id}': {fs_err}")
                if self.is_production():
                    raise ProductionPersistenceError(f"Cloud Firestore fetch failed in production: {fs_err}") from fs_err
                return None

        # 2. PostgreSQL
        if self.manager.is_postgres:
            try:
                query = """
                SELECT snapshot_json FROM procurement_history
                WHERE procurement_id = %s AND (user_id = %s OR firebase_uid = %s)
                """
                row = self.manager.fetch_one(query, (procurement_id, user_id, target_uid))
                if row and row.get("snapshot_json"):
                    return json.loads(row["snapshot_json"])
                return None
            except Exception as e:
                logger.error(f"[POSTGRESQL] Error fetching history '{procurement_id}': {e}")
                if self.is_production():
                    raise ProductionPersistenceError(f"PostgreSQL fetch failed in production: {e}") from e
                return None

        # 3. Development SQLite Fallback
        # STRICTLY PROHIBITED in production
        if self.is_production():
            raise ProductionPersistenceError(
                "Production environment requires durable persistence (Cloud Firestore or PostgreSQL/Neon). "
                "Local SQLite persistence is strictly prohibited in production."
            )

        try:
            query = """
            SELECT snapshot_json FROM procurement_history
            WHERE procurement_id = ? AND (user_id = ? OR firebase_uid = ?)
            """
            row = self.manager.fetch_one(query, (procurement_id, user_id, target_uid))
            if row and row.get("snapshot_json"):
                return json.loads(row["snapshot_json"])
            return None
        except Exception as e:
            logger.error(f"[SQLITE] Error fetching development history '{procurement_id}': {e}")
            return None

    def delete_snapshot(
        self,
        procurement_id: str,
        user_id: str,
        firebase_uid: Optional[str] = None
    ) -> bool:
        """
        Deletes a procurement history snapshot owned by the user.
        """
        if not procurement_id or not user_id:
            return False

        if self.is_production() and not self.is_durable_storage_available():
            raise ProductionPersistenceError(
                "Production environment requires durable persistence (Cloud Firestore or PostgreSQL/Neon). "
                "Local SQLite persistence is strictly prohibited in production."
            )

        target_uid = firebase_uid or user_id

        # 1. Cloud Firestore
        if self.has_firestore():
            try:
                from backend.app.services.firestore_service import firestore_service
                db = firestore_service._get_client()
                if db:
                    doc_ref = db.collection("users").document(target_uid).collection("procurement_history").document(procurement_id)
                    snap = doc_ref.get()
                    if snap.exists:
                        doc_ref.delete()
                        # Also delete from Postgres if mirrored
                        if self.manager.is_postgres:
                            try:
                                with self.get_connection() as conn:
                                    cursor = conn.cursor()
                                    cursor.execute("""
                                    DELETE FROM procurement_history
                                    WHERE procurement_id = %s AND (user_id = %s OR firebase_uid = %s)
                                    """, (procurement_id, user_id, target_uid))
                                    conn.commit()
                            except Exception:
                                pass
                        return True
                return False
            except Exception as fs_err:
                logger.error(f"[FIRESTORE] Error deleting history '{procurement_id}': {fs_err}")
                if self.is_production():
                    raise ProductionPersistenceError(f"Cloud Firestore delete failed in production: {fs_err}") from fs_err
                return False

        # 2. PostgreSQL
        if self.manager.is_postgres:
            try:
                deleted = False
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                    DELETE FROM procurement_history
                    WHERE procurement_id = %s AND (user_id = %s OR firebase_uid = %s)
                    """, (procurement_id, user_id, target_uid))
                    conn.commit()
                    deleted = cursor.rowcount > 0
                return deleted
            except Exception as e:
                logger.error(f"[POSTGRESQL] Error deleting history '{procurement_id}': {e}")
                if self.is_production():
                    raise ProductionPersistenceError(f"PostgreSQL delete failed in production: {e}") from e
                return False

        # 3. Development SQLite Fallback
        # STRICTLY PROHIBITED in production
        if self.is_production():
            raise ProductionPersistenceError(
                "Production environment requires durable persistence (Cloud Firestore or PostgreSQL/Neon). "
                "Local SQLite persistence is strictly prohibited in production."
            )

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                DELETE FROM procurement_history
                WHERE procurement_id = ? AND (user_id = ? OR firebase_uid = ?)
                """, (procurement_id, user_id, target_uid))
                conn.commit()
                deleted = cursor.rowcount > 0
            return deleted
        except Exception as e:
            logger.error(f"[SQLITE] Error deleting development history '{procurement_id}': {e}")
            return False


# Singleton instance
history_repository = ProcurementHistoryRepository()

def get_history_repository() -> ProcurementHistoryRepository:
    return history_repository
