import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from backend.app.services.providers.provider_interface import EvidenceProvider
from backend.app.models.responses import (
    FreshnessState,
    VerificationMethod,
    ExtendedVerificationStatus,
    BisCertificationStatus
)

class BisEvidenceProvider(EvidenceProvider):
    """
    Official Bureau of Indian Standards (BIS) Evidence Adapter.
    
    Safety & Compliance Rules:
    - Never bypasses, scrapes, or circumvents official BIS portal CAPTCHAs or security controls.
    - Honest about programmatic verification limits: reports can_auto_verify = False for unauthenticated portal lookups.
    - Evaluates CML / CRS format legitimacy.
    - Tracks freshness: checks explicit validity dates if provided; defaults to UNKNOWN.
    - Generates guided buyer verification workflow.
    """

    OFFICIAL_BIS_PORTAL_URL = "https://www.manakonline.in/MANAK/conFormityAssessmentAction"

    @property
    def provider_id(self) -> str:
        return "PROVIDER-BIS-MANAK"

    @property
    def provider_name(self) -> str:
        return "Bureau of Indian Standards (BIS) Conformity Assessment Interface"

    @property
    def can_auto_verify(self) -> bool:
        # Public BIS portal requires interactive CAPTCHA / session.
        # BharatBuy operates ethically and does not scrape or bypass access controls.
        return False

    def search(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Without an authenticated BIS enterprise API key, programmatic search is restricted
        return []

    def fetch(self, reference_id: str) -> Optional[Dict[str, Any]]:
        # Format check for CML or CRS
        clean_ref = reference_id.strip().upper()
        if re.match(r'^(CML|CM/L)[- ]?\d{7,10}$', clean_ref) or re.match(r'^R-\d{8}$', clean_ref):
            return {
                "reference_id": clean_ref,
                "scheme": "Scheme I (ISI Mark)" if "CML" in clean_ref or "CM/L" in clean_ref else "CRS (Scheme II)",
                "official_portal_url": self.OFFICIAL_BIS_PORTAL_URL,
                "status": BisCertificationStatus.REQUIRES_LIVE_VERIFICATION.value
            }
        return None

    def validate(self, evidence: Dict[str, Any]) -> Tuple[str, float, Optional[str]]:
        ref_id = evidence.get("reference_id") or ""
        valid_until = evidence.get("valid_until") or evidence.get("expires_at")
        buyer_verified = evidence.get("buyer_verified", False)
        
        # If buyer has explicitly confirmed on the official portal with audit trail
        if buyer_verified:
            return (ExtendedVerificationStatus.CONFIRMED.value, 0.95, "Confirmed by buyer via official BIS portal audit.")

        # Check reference formatting
        if ref_id and (re.search(r'\b(CML[- ]\d+|CM/L[- ]\d+|R-\d+)\b', ref_id)):
            # Check for expiration if explicit date exists
            freshness_val = self.freshness(evidence)
            if freshness_val == FreshnessState.STALE.value:
                return (
                    ExtendedVerificationStatus.EXPIRED.value,
                    0.30,
                    f"BIS license reference {ref_id} has expired validity ({valid_until})."
                )
            return (
                ExtendedVerificationStatus.REQUIRES_VERIFICATION.value,
                0.75,
                f"Documented BIS reference {ref_id} requires live verification on official portal."
            )
        
        return (ExtendedVerificationStatus.PARTIAL.value, 0.40, "No specific BIS CML reference provided.")

    def freshness(self, evidence: Dict[str, Any]) -> str:
        """
        Determines freshness strictly based on recorded expiry/retrieval dates.
        Never invents arbitrary expiry periods for statutory licenses.
        """
        valid_until = evidence.get("valid_until") or evidence.get("expires_at")
        if not valid_until:
            return FreshnessState.UNKNOWN.value

        try:
            # Parse ISO date or YYYY-MM-DD
            if "T" in str(valid_until):
                exp_dt = datetime.fromisoformat(str(valid_until).replace("Z", "+00:00"))
            else:
                exp_dt = datetime.strptime(str(valid_until), "%Y-%m-%d").replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            delta_days = (exp_dt - now).days

            if delta_days < 0:
                return FreshnessState.STALE.value
            elif delta_days < 60:
                return FreshnessState.AGING.value
            else:
                return FreshnessState.CURRENT.value
        except Exception:
            return FreshnessState.UNKNOWN.value

    def provenance(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        ref_id = evidence.get("reference_id", "N/A")
        return {
            "provider_id": self.provider_id,
            "provider_name": self.provider_name,
            "official_url": self.OFFICIAL_BIS_PORTAL_URL,
            "reference_id": ref_id,
            "verification_mode": "MANUAL_GUIDED_WORKFLOW",
            "statutory_authority": "Bureau of Indian Standards Act, 2016",
            "retrieved_at": evidence.get("retrieved_at")
        }

    def get_buyer_verification_workflow(
        self,
        reference_id: Optional[str],
        standard_code: Optional[str],
        product_category: Optional[str],
        source_name: Optional[str]
    ) -> Dict[str, Any]:
        """
        Constructs the structured buyer checklist and instructions.
        """
        return {
            "status": "REQUIRES_MANUAL_VERIFICATION",
            "can_auto_verify": False,
            "official_verification_url": self.OFFICIAL_BIS_PORTAL_URL,
            "reference_id": reference_id or "CHECK_REQUIRED",
            "standard_code": standard_code or "N/A",
            "source_name": source_name or "Unknown Supplier",
            "checks": [
                "License/reference exists on official BIS portal",
                "Product category matches certified manufacturing scope",
                "Applicable Indian Standard matches cited IS code",
                "License is currently active and unexpired",
                "Manufacturer name and factory site address match supplier"
            ],
            "instructions": (
                f"Open the official BIS portal ({self.OFFICIAL_BIS_PORTAL_URL}), enter reference "
                f"'{reference_id or 'CM/L-...'}' in the Conformity Assessment database, "
                f"and confirm each check before issuing buyer approval."
            )
        }
