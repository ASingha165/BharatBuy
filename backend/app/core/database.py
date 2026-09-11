import os
import sqlite3
from typing import List, Dict, Any, Optional, Generator, Tuple
from contextlib import contextmanager
from urllib.parse import urlparse
from backend.app.core.config import settings
from backend.app.core.logging import logger

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


class DatabaseManager:
    """
    Dual-engine Database Manager supporting:
    1. Neon / Cloud SQL PostgreSQL (when DATABASE_URL is configured)
    2. Local SQLite (when DATABASE_URL is unset/empty) - 100% backward compatible
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        sqlite_path: Optional[str] = None,
        force_sqlite: bool = False
    ):
        self._custom_database_url = database_url
        self._custom_sqlite_path = sqlite_path
        self._force_sqlite = force_sqlite

    @property
    def database_url(self) -> Optional[str]:
        if self._force_sqlite:
            return None
        if self._custom_database_url is not None:
            raw = self._custom_database_url.strip()
            return raw if raw else None
        raw_url = settings.DATABASE_URL
        if raw_url and raw_url.strip():
            return raw_url.strip()
        return None

    @property
    def is_postgres(self) -> bool:
        url = self.database_url
        return bool(url and (url.startswith("postgresql://") or url.startswith("postgres://")))

    @property
    def engine_name(self) -> str:
        return "postgresql" if self.is_postgres else "sqlite"

    @property
    def sqlite_path(self) -> str:
        path = self._custom_sqlite_path or settings.DATABASE_PATH
        if not os.path.isabs(path):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            path = os.path.join(base_dir, path)
        return path

    def get_sanitized_status(self) -> Dict[str, Any]:
        """
        Returns database engine status without exposing credentials or passwords.
        """
        if self.is_postgres:
            try:
                parsed = urlparse(self.database_url)
                return {
                    "engine": "postgresql",
                    "host": parsed.hostname,
                    "port": parsed.port or 5432,
                    "database": parsed.path.lstrip("/"),
                    "user": parsed.username,
                    "connected": self.check_health()
                }
            except Exception:
                return {
                    "engine": "postgresql",
                    "connected": self.check_health()
                }
        else:
            return {
                "engine": "sqlite",
                "path": self.sqlite_path,
                "connected": self.check_health()
            }

    @contextmanager
    def get_connection(self) -> Generator[Any, None, None]:
        """
        Context manager yielding an active database connection.
        Closes connection cleanly upon context exit.
        """
        if self.is_postgres:
            if not PSYCOPG2_AVAILABLE:
                raise RuntimeError("psycopg2 is required for PostgreSQL connections but is not installed.")
            conn = psycopg2.connect(self.database_url)
            try:
                yield conn
            finally:
                conn.close()
        else:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()

    def format_query(self, query: str) -> str:
        """
        Translates SQL query placeholders.
        SQLite uses '?', PostgreSQL (psycopg2) uses '%s'.
        """
        if self.is_postgres:
            return query.replace("?", "%s")
        return query

    def check_health(self) -> bool:
        """
        Executes a basic ping query to verify database health.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                res = cursor.fetchone()
                return bool(res)
        except Exception as e:
            logger.error(f"[{self.engine_name.upper()}] Health check failed: {e}")
            return False

    def fetch_all(self, query: str, params: Tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
        """
        Executes a SELECT query and returns rows as a list of dictionaries.
        """
        formatted = self.format_query(query)
        try:
            with self.get_connection() as conn:
                if self.is_postgres:
                    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        cursor.execute(formatted, params)
                        rows = cursor.fetchall()
                        return [dict(r) for r in rows]
                else:
                    cursor = conn.cursor()
                    cursor.execute(formatted, params)
                    rows = cursor.fetchall()
                    return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"[{self.engine_name.upper()}] Error executing fetch_all: {e}")
            return []

    def fetch_one(self, query: str, params: Tuple[Any, ...] = ()) -> Optional[Dict[str, Any]]:
        """
        Executes a SELECT query and returns a single row as a dictionary.
        """
        formatted = self.format_query(query)
        try:
            with self.get_connection() as conn:
                if self.is_postgres:
                    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        cursor.execute(formatted, params)
                        row = cursor.fetchone()
                        return dict(row) if row else None
                else:
                    cursor = conn.cursor()
                    cursor.execute(formatted, params)
                    row = cursor.fetchone()
                    return dict(row) if row else None
        except Exception as e:
            logger.error(f"[{self.engine_name.upper()}] Error executing fetch_one: {e}")
            return None

    def execute(self, query: str, params: Tuple[Any, ...] = ()) -> int:
        """
        Executes an INSERT, UPDATE, or DELETE query and commits transaction.
        Returns the affected row count.
        """
        formatted = self.format_query(query)
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(formatted, params)
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"[{self.engine_name.upper()}] Error executing statement: {e}")
            raise


# Global singleton instance
db_manager = DatabaseManager()
