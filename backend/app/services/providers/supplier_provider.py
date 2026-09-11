from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from backend.app.services.providers.provider_interface import EvidenceProvider
from backend.app.models.responses import (
    FreshnessState,
    VerificationMethod,
    ExtendedVerificationStatus
)

class SupplierEvidenceProvider(EvidenceProvider):
    """
    Supplier-Declared Evidence Provider.
    Handles self-declared vendor capabilities, commercial distributor channels,
    and Mill Test Certificates (MTC) supplied per dispatch.
    
    Safety Guarantee:
    Vendor self-declarations are never upgraded to verified statutory certification
    without independent portal confirmation.
    """

    @property
    def provider_id(self) -> str:
        return "PROVIDER-SUPPLIER-DECLARATION"

    @property
    def provider_name(self) -> str:
        return "Supplier Declaration & Mill Test Certificate (MTC) Interface"

    @property
    def can_auto_verify(self) -> bool:
        return False

    def search(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []

    def fetch(self, reference_id: str) -> Optional[Dict[str, Any]]:
        return {
            "reference_id": reference_id,
            "channel_type": "COMMERCIAL_DISTRIBUTION",
            "statutory_claim": "UNVERIFIED_DECLARATION"
        }

    def validate(self, evidence: Dict[str, Any]) -> Tuple[str, float, Optional[str]]:
        has_mtc = evidence.get("has_mtc", False)
        is_oem_auth = evidence.get("is_oem_authorized", False)

        if is_oem_auth and has_mtc:
            return (
                ExtendedVerificationStatus.PARTIAL.value,
                0.65,
                "Vendor possesses OEM authorization and per-dispatch MTC; factory CML verification recommended."
            )
        elif has_mtc:
            return (
                ExtendedVerificationStatus.REQUIRES_VERIFICATION.value,
                0.50,
                "Self-declared MTC requires NABL lab validation before material acceptance."
            )
        
        return (
            ExtendedVerificationStatus.REQUIRES_VERIFICATION.value,
            0.40,
            "Commercial distributor channel without primary factory certification."
        )

    def freshness(self, evidence: Dict[str, Any]) -> str:
        certificate_date = evidence.get("certificate_date")
        if not certificate_date:
            return FreshnessState.UNKNOWN.value

        try:
            cert_dt = datetime.fromisoformat(str(certificate_date).replace("Z", "+00:00"))
            delta_days = (datetime.now(timezone.utc) - cert_dt).days
            if delta_days > 180:
                return FreshnessState.STALE.value
            elif delta_days > 90:
                return FreshnessState.AGING.value
            return FreshnessState.CURRENT.value
        except Exception:
            return FreshnessState.UNKNOWN.value

    def provenance(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "provider_name": self.provider_name,
            "channel": "COMMERCIAL_VENDOR",
            "verification_method": VerificationMethod.MANUAL.value,
            "confidence": 0.45
        }
