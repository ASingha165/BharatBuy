import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.database import DatabaseManager, db_manager, PSYCOPG2_AVAILABLE

if PSYCOPG2_AVAILABLE:
    import psycopg2
    IntegrityErrors = (sqlite3.IntegrityError, psycopg2.IntegrityError)
else:
    IntegrityErrors = (sqlite3.IntegrityError,)


class UserRepository:
    """
    User Account & Identity Data Access Layer.
    Supports seamless dual-engine operation:
    - Neon PostgreSQL when DATABASE_URL is configured (supports firebase_uid)
    - Local SQLite fallback when DATABASE_URL is absent (preserves existing 7-column schema without modifying SQLite)
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
    def db_path(self) -> str:
        return self.manager.sqlite_path

    @property
    def engine_name(self) -> str:
        return self.manager.engine_name

    def get_connection(self):
        return self.manager.get_connection()

    def _init_db(self) -> None:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if self.manager.is_postgres:
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id VARCHAR(128) PRIMARY KEY,
                        name VARCHAR(150) NOT NULL,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        organization VARCHAR(200) NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        firebase_uid VARCHAR(128) UNIQUE,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                    CREATE INDEX IF NOT EXISTS idx_users_firebase_uid ON users(firebase_uid);
                    """)
                    conn.commit()
                else:
                    # SQLite: strictly preserve existing schema, only create if table doesn't exist
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        organization TEXT NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """)
                    cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
                    """)
                    conn.commit()
        except Exception as e:
            logger.error(f"[{self.engine_name.upper()}] Failed to initialize users table in database: {e}")

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        try:
            normalized_email = email.strip().lower()
            if self.manager.is_postgres:
                return self.manager.fetch_one("""
                SELECT id, name, email, organization, password_hash, firebase_uid, created_at, updated_at
                FROM users
                WHERE email = ?
                """, (normalized_email,))
            else:
                row = self.manager.fetch_one("""
                SELECT id, name, email, organization, password_hash, created_at, updated_at
                FROM users
                WHERE email = ?
                """, (normalized_email,))
                if row:
                    row["firebase_uid"] = None
                return row
        except Exception as e:
            logger.error(f"[{self.engine_name.upper()}] Error fetching user by email: {e}")
            return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            if self.manager.is_postgres:
                return self.manager.fetch_one("""
                SELECT id, name, email, organization, password_hash, firebase_uid, created_at, updated_at
                FROM users
                WHERE id = ?
                """, (user_id,))
            else:
                row = self.manager.fetch_one("""
                SELECT id, name, email, organization, password_hash, created_at, updated_at
                FROM users
                WHERE id = ?
                """, (user_id,))
                if row:
                    row["firebase_uid"] = None
                return row
        except Exception as e:
            logger.error(f"[{self.engine_name.upper()}] Error fetching user by ID: {e}")
            return None

    def create_user(
        self,
        user_id: str,
        name: str,
        email: str,
        organization: str,
        password_hash: str,
        firebase_uid: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        try:
            normalized_email = email.strip().lower()
            now_iso = datetime.now(timezone.utc).isoformat()
            if self.manager.is_postgres:
                query = """
                INSERT INTO users (id, name, email, organization, password_hash, firebase_uid, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                self.manager.execute(
                    query,
                    (user_id, name.strip(), normalized_email, organization.strip(), password_hash, firebase_uid, now_iso, now_iso)
                )
            else:
                query = """
                INSERT INTO users (id, name, email, organization, password_hash, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                self.manager.execute(
                    query,
                    (user_id, name.strip(), normalized_email, organization.strip(), password_hash, now_iso, now_iso)
                )
            return self.get_user_by_id(user_id)
        except IntegrityErrors:
            logger.warning(f"Integrity error creating user with email {email}: duplicate email or id")
            return None
    def get_user_by_firebase_uid(self, firebase_uid: str) -> Optional[Dict[str, Any]]:
        try:
            clean_uid = firebase_uid.strip()
            if self.manager.is_postgres:
                return self.manager.fetch_one("""
                SELECT id, name, email, organization, password_hash, firebase_uid, created_at, updated_at
                FROM users
                WHERE firebase_uid = ?
                """, (clean_uid,))
            else:
                # In SQLite fallback, attempt check if column exists
                try:
                    return self.manager.fetch_one("""
                    SELECT id, name, email, organization, password_hash, firebase_uid, created_at, updated_at
                    FROM users
                    WHERE firebase_uid = ?
                    """, (clean_uid,))
                except Exception:
                    return None
        except Exception as e:
            logger.error(f"[{self.engine_name.upper()}] Error fetching user by Firebase UID: {e}")
            return None

    def upsert_firebase_user(
        self,
        firebase_uid: str,
        email: str,
        name: Optional[str] = None,
        organization: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Creates or updates a user profile anchored to a verified Firebase UID.
        Prevents duplicate user accounts and safely links existing accounts by email.
        """
        import secrets
        clean_uid = firebase_uid.strip()
        clean_email = email.strip().lower()
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Check if user already exists by firebase_uid
        user = self.get_user_by_firebase_uid(clean_uid)
        if user:
            # Update name / organization if provided
            updates = []
            params = []
            if name and name.strip() and name.strip() != user.get("name"):
                updates.append("name = ?")
                params.append(name.strip())
            if organization and organization.strip() and organization.strip() != user.get("organization"):
                updates.append("organization = ?")
                params.append(organization.strip())
            if updates:
                updates.append("updated_at = ?")
                params.append(now_iso)
                params.append(user["id"])
                query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
                self.manager.execute(query, tuple(params))
            return self.get_user_by_id(user["id"])

        # 2. Check if user exists by email (link existing account)
        user_by_email = self.get_user_by_email(clean_email)
        if user_by_email:
            try:
                self.manager.execute(
                    "UPDATE users SET firebase_uid = ?, updated_at = ? WHERE id = ?",
                    (clean_uid, now_iso, user_by_email["id"])
                )
            except Exception as e:
                logger.warning(f"[{self.engine_name.upper()}] Could not set firebase_uid on user {clean_email}: {e}")
            return self.get_user_by_id(user_by_email["id"])

        # 3. Create new user profile for this Firebase user
        user_id = f"usr_{secrets.token_hex(8)}"
        display_name = (name.strip() if name and name.strip() else clean_email.split("@")[0].title())
        org_name = (organization.strip() if organization and organization.strip() else "Startup Procurement")
        pwd_hash = "FIREBASE_MANAGED_AUTH"

        return self.create_user(
            user_id=user_id,
            name=display_name,
            email=clean_email,
            organization=org_name,
            password_hash=pwd_hash,
            firebase_uid=clean_uid
        )

    def delete_user_by_email(self, email: str) -> bool:
        try:
            normalized_email = email.strip().lower()
            count = self.manager.execute("DELETE FROM users WHERE email = ?", (normalized_email,))
            return count > 0
        except Exception as e:
            logger.error(f"[{self.engine_name.upper()}] Error deleting user: {e}")
            return False

    def delete_users_by_emails(self, emails: list[str]) -> bool:
        if not emails:
            return True
        try:
            cleaned = [e.strip().lower() for e in emails if e and e.strip()]
            if not cleaned:
                return True
            placeholders = ", ".join(["?"] * len(cleaned))
            query = f"DELETE FROM users WHERE email IN ({placeholders})"
            self.manager.execute(query, tuple(cleaned))
            return True
        except Exception as e:
            logger.error(f"[{self.engine_name.upper()}] Error batch deleting users: {e}")
            return False

    def delete_user_by_firebase_uid(self, uid: str) -> bool:
        try:
            clean_uid = uid.strip()
            count = self.manager.execute("DELETE FROM users WHERE firebase_uid = ?", (clean_uid,))
            return count > 0
        except Exception as e:
            logger.error(f"[{self.engine_name.upper()}] Error deleting user by UID: {e}")
            return False
