from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple

class EvidenceProvider(ABC):
    """
    Abstract Evidence Provider Interface for BharatBuy (Phase 4).
    Decouples the procurement intelligence engine from specific external data sources
    and prevents vendor lock-in.

    Conceptual Operations:
    - search: Search for records matching query parameters.
    - fetch: Retrieve full record for a specific identifier.
    - validate: Verify authenticity, schema conformance, and legitimacy.
    - freshness: Determine temporal state (CURRENT, AGING, STALE, UNKNOWN).
    - provenance: Generate traceable audit origin metadata.
    """

    @property
    @abstractmethod
    def provider_id(self) -> str:
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def can_auto_verify(self) -> bool:
        """Returns True if this provider can perform unassisted live programmatic verification."""
        pass

    @abstractmethod
    def search(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Searches the provider's authoritative repository."""
        pass

    @abstractmethod
    def fetch(self, reference_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves an evidence record by unique reference ID."""
        pass

    @abstractmethod
    def validate(self, evidence: Dict[str, Any]) -> Tuple[str, float, Optional[str]]:
        """
        Validates the evidence item.
        Returns: (verification_status, confidence_score, explanation_note)
        """
        pass

    @abstractmethod
    def freshness(self, evidence: Dict[str, Any]) -> str:
        """
        Evaluates freshness state: 'CURRENT', 'AGING', 'STALE', or 'UNKNOWN'.
        Never invents arbitrary expiry dates.
        """
        pass

    @abstractmethod
    def provenance(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Returns provenance dictionary identifying source organization, method, and URI."""
        pass
