import os
from typing import List, Optional, Dict, Any
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.database import DatabaseManager, db_manager

class StandardsRepository:
    """
    Data Access Layer for Indian Standards catalog.
    Supports seamless dual-engine operation:
    - Neon PostgreSQL when DATABASE_URL is configured
    - Local SQLite fallback when DATABASE_URL is absent
    """
    def __init__(self, db_path: Optional[str] = None, manager: Optional[DatabaseManager] = None):
        if manager:
            self.manager = manager
        elif db_path:
            self.manager = DatabaseManager(sqlite_path=db_path)
        else:
            self.manager = db_manager

    @property
    def db_path(self) -> str:
        return self.manager.sqlite_path

    @property
    def engine_name(self) -> str:
        return self.manager.engine_name

    def get_connection(self):
        return self.manager.get_connection()

    def check_health(self) -> bool:
        try:
            return self.manager.check_health()
        except Exception as e:
            logger.error(f"[{self.engine_name.upper()}] Database health check failed: {e}")
            return False

    def get_total_count(self) -> int:
        try:
            res = self.manager.fetch_one("SELECT COUNT(*) AS cnt FROM standards")
            if res:
                # Can be 'cnt' or 'count' depending on engine
                return res.get("cnt") or res.get("count") or list(res.values())[0] or 0
            return 0
        except Exception as e:
            logger.error(f"[{self.engine_name.upper()}] Error fetching total count: {e}")
            return 0

    def get_all_standards(self) -> List[Dict[str, Any]]:
        try:
            return self.manager.fetch_all("""
            SELECT standard_id, is_code, title, department, scope_summary, key_specifications, testing_requirements, status, publication_year
            FROM standards
            """)
        except Exception as e:
            logger.error(f"[{self.engine_name.upper()}] Error fetching all standards: {e}")
            return []

    def get_standard_by_id(self, standard_id: str) -> Optional[Dict[str, Any]]:
        try:
            return self.manager.fetch_one("""
            SELECT standard_id, is_code, title, department, scope_summary, key_specifications, testing_requirements, status, publication_year
            FROM standards
            WHERE standard_id = ? OR is_code = ?
            """, (standard_id, standard_id))
        except Exception as e:
            logger.error(f"[{self.engine_name.upper()}] Error fetching standard by ID '{standard_id}': {e}")
            return None

    def get_standards_by_ids(self, standard_ids: List[str]) -> List[Dict[str, Any]]:
        if not standard_ids:
            return []
        try:
            placeholders = ",".join(["?"] * len(standard_ids))
            query = f"""
            SELECT standard_id, is_code, title, department, scope_summary, key_specifications, testing_requirements, status, publication_year
            FROM standards
            WHERE standard_id IN ({placeholders})
            """
            return self.manager.fetch_all(query, tuple(standard_ids))
        except Exception as e:
            logger.error(f"[{self.engine_name.upper()}] Error fetching standards by IDs: {e}")
            return []
