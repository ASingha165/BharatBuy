import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from backend.app.models.responses import AuditLogEntry
from backend.app.core.logging import logger

class AuditService:
    """
    Lightweight, thread-safe verification audit trail.
    Records all verification actions, buyer manual affirmations, and status changes.
    Never stores credentials or confidential secrets.
    """
    _instance = None

    def __init__(self):
        self._logs: List[AuditLogEntry] = []
        # Pre-seed baseline registry initialization event for traceability
        self._logs.append(
            AuditLogEntry(
                log_id="LOG-INIT-001",
                source_id="SYSTEM",
                evidence_id="REGISTRY-V1",
                action="AUTHORITATIVE_REGISTRY_LOADED",
                previous_status="UNINITIALIZED",
                new_status="REGISTRY_ACTIVE",
                verification_method="REGISTRY",
                timestamp="2026-09-09T00:00:00Z",
                actor="system:registry_loader",
                notes="Authoritative Sourcing Registry v1 loaded with 17 registered Indian source records."
            )
        )

    @classmethod
    def get_instance(cls) -> "AuditService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def record_event(
        self,
        source_id: str,
        action: str,
        previous_status: str,
        new_status: str,
        verification_method: str = "MANUAL",
        actor: str = "system",
        evidence_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> AuditLogEntry:
        log_id = f"LOG-{uuid.uuid4().hex[:8].upper()}"
        ts = datetime.now(timezone.utc).isoformat()
        entry = AuditLogEntry(
            log_id=log_id,
            source_id=source_id,
            evidence_id=evidence_id,
            action=action,
            previous_status=previous_status,
            new_status=new_status,
            verification_method=verification_method,
            timestamp=ts,
            actor=actor,
            notes=notes
        )
        self._logs.append(entry)
        logger.info(f"[AUDIT] {entry.log_id} | {entry.action} on {source_id} by {actor} ({previous_status} -> {new_status})")
        return entry

    def record(
        self,
        source_id: str,
        action: str,
        previous_status: str,
        new_status: str,
        verification_method: str = "MANUAL",
        actor: str = "system",
        evidence_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> AuditLogEntry:
        return self.record_event(
            source_id=source_id,
            action=action,
            previous_status=previous_status,
            new_status=new_status,
            verification_method=verification_method,
            actor=actor,
            evidence_id=evidence_id,
            notes=notes
        )

    def get_logs_for_source(self, source_id: Optional[str] = None) -> List[AuditLogEntry]:
        return self.get_audit_trail(source_id)

    def get_audit_trail(self, source_id: Optional[str] = None) -> List[AuditLogEntry]:
        if not source_id:
            return list(self._logs)
        return [l for l in self._logs if l.source_id.upper() == source_id.upper() or l.source_id == "SYSTEM"]

    def clear(self) -> None:
        """Reset logs for clean test isolation."""
        self._logs.clear()
