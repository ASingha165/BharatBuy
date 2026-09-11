from typing import Dict, Optional, List, Any
from backend.app.services.providers.provider_interface import EvidenceProvider
from backend.app.services.providers.bis_provider import BisEvidenceProvider
from backend.app.services.providers.government_provider import GovernmentRecordProvider
from backend.app.services.providers.supplier_provider import SupplierEvidenceProvider
from backend.app.models.responses import EvidenceType

class EvidenceProviderRegistry:
    """
    Central Registry for Authoritative Evidence Providers.
    Allows runtime provider dispatching, future authorized API plugin injection,
    and unified provenance tracking.
    """
    _instance = None

    def __init__(self):
        self._providers: Dict[str, EvidenceProvider] = {
            "BIS": BisEvidenceProvider(),
            "GOVERNMENT": GovernmentRecordProvider(),
            "SUPPLIER": SupplierEvidenceProvider()
        }

    @classmethod
    def get_instance(cls) -> "EvidenceProviderRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_provider(self, key: str, provider: EvidenceProvider) -> None:
        self._providers[key.upper()] = provider

    def get_provider(self, provider_key: str) -> Optional[EvidenceProvider]:
        return self._providers.get(provider_key.upper())

    def get_bis_provider(self) -> BisEvidenceProvider:
        return self._providers["BIS"]  # type: ignore

    def get_government_provider(self) -> GovernmentRecordProvider:
        return self._providers["GOVERNMENT"]  # type: ignore

    def get_supplier_provider(self) -> SupplierEvidenceProvider:
        return self._providers["SUPPLIER"]  # type: ignore

    def get_provider_for_evidence_type(self, evidence_type: str) -> Optional[EvidenceProvider]:
        if evidence_type in [EvidenceType.BIS_LICENSE.value, EvidenceType.BIS_STANDARD.value]:
            return self.get_bis_provider()
        elif evidence_type in [EvidenceType.GOVERNMENT_RECORD.value, EvidenceType.SOURCE_REGISTRY.value, EvidenceType.LOCATION.value]:
            return self.get_government_provider()
        elif evidence_type in [EvidenceType.VENDOR_DECLARATION.value, EvidenceType.PRODUCT_CAPABILITY.value]:
            return self.get_supplier_provider()
        return None

    def list_providers(self) -> List[Dict[str, Any]]:
        return [
            {
                "provider_id": p.provider_id,
                "provider_name": p.provider_name,
                "can_auto_verify": p.can_auto_verify
            }
            for p in self._providers.values()
        ]

def get_provider_registry() -> EvidenceProviderRegistry:
    return EvidenceProviderRegistry.get_instance()
