import re
from typing import List, Dict, Any, Optional
from backend.app.services.preprocessing_service import PreprocessingService
from backend.app.services.feature_service import FeatureService
from backend.app.models.requests import ProcurementRequirementItem
from backend.app.models.responses import NormalizedRequirementItem
from backend.app.core.logging import logger

class NormalizationService:
    """
    Normalizes raw procurement line items and unstructured specifications
    into structured, validated technical representations without hallucinating standards.
    """

    def __init__(
        self,
        preprocessing_service: Optional[PreprocessingService] = None,
        feature_service: Optional[FeatureService] = None
    ):
        self.preprocessing = preprocessing_service or PreprocessingService()
        self.feature_service = feature_service or FeatureService(self.preprocessing)

    def normalize_item(self, req: ProcurementRequirementItem, index: int = 1) -> NormalizedRequirementItem:
        raw_text = f"{req.item} {req.specifications or ''}"
        features = self.feature_service.extract_features(raw_text)
        
        # Determine product category
        products = features.get("products", [])
        category = products[0].title() if products else "General Equipment"
        
        # Extract materials and applications
        materials = features.get("materials", [])
        units = features.get("units", {})
        
        # Build clean search terms
        keywords = features.get("keywords", [])
        search_terms = list(dict.fromkeys(keywords))  # deduplicate preserving order

        # Inferred standard requirements based purely on verified physical properties
        inferred_specs: List[str] = []
        if units.get("voltage"):
            inferred_specs.append(f"Operating Voltage: {', '.join(units['voltage'])}")
        if units.get("current"):
            inferred_specs.append(f"Rated Current: {', '.join(units['current'])}")
        if units.get("power"):
            inferred_specs.append(f"Power Rating: {', '.join(units['power'])}")
        if materials:
            inferred_specs.append(f"Constituent Materials: {', '.join(m.upper() for m in materials)}")

        # Mandatory certifications requested
        mandatory_certs = list(req.required_certifications or [])
        raw_lower = raw_text.lower()
        if "isi" in raw_lower or "isi mark" in raw_lower:
            if "ISI Mark" not in mandatory_certs:
                mandatory_certs.append("ISI Mark")
        if "crs" in raw_lower or "compulsory registration" in raw_lower:
            if "CRS" not in mandatory_certs:
                mandatory_certs.append("CRS")
        if "bis" in raw_lower and not mandatory_certs:
            mandatory_certs.append("BIS Certification")

        normalized_spec = req.specifications.strip() if req.specifications else f"Standard procurement specification for {req.item}"

        return NormalizedRequirementItem(
            item_name=req.item.strip(),
            category=category,
            quantity=float(req.quantity if req.quantity and req.quantity > 0 else 1.0),
            unit=req.unit.strip() if req.unit else "units",
            specifications=normalized_spec,
            mandatory_certifications=mandatory_certs,
            inferred_standard_requirements=inferred_specs,
            search_terms=search_terms
        )

    def parse_natural_language_requirements(self, text: str) -> List[ProcurementRequirementItem]:
        """
        Parses multi-item natural language descriptions (e.g. from case studies or tender briefs)
        into discrete ProcurementRequirementItem line items.
        """
        if not text or not text.strip():
            return []

        lines = [line.strip() for line in text.split("\n") if line.strip()]
        items: List[ProcurementRequirementItem] = []

        # Check if text is a bulleted or numbered list
        bullet_pattern = re.compile(r'^(?:[-*•]|\d+[\.\)])\s*(.+)$')
        bullet_items = [bullet_pattern.match(l).group(1) for l in lines if bullet_pattern.match(l)]

        if bullet_items:
            for b in bullet_items:
                items.append(self._parse_single_phrase_to_item(b))
        else:
            # Check for comma-separated or sentence-separated item clauses
            clauses = re.split(r'[;.]|,\s*(?:and\s+)?(?=[a-zA-Z0-9\s]{4,})', text)
            for c in clauses:
                c_clean = c.strip()
                if len(c_clean) > 5 and not c_clean.lower().startswith("we need") and not c_clean.lower().startswith("we are"):
                    items.append(self._parse_single_phrase_to_item(c_clean))

        return items if items else [self._parse_single_phrase_to_item(text)]

    def _parse_single_phrase_to_item(self, phrase: str) -> ProcurementRequirementItem:
        # Extract quantity if specified (e.g. 100 meters, 50 units, 20 kg)
        qty_match = re.search(r'\b(\d+(?:\.\d+)?)\s*(meters?|units?|nos?|pcs?|kg|tonnes?|boxes?|litres?|sets?)\b', phrase, re.IGNORECASE)
        qty = float(qty_match.group(1)) if qty_match else 1.0
        unit = qty_match.group(2).lower() if qty_match else "units"
        
        item_title = phrase.strip()
        # Clean leading words like "buy", "purchase", "procure", "install"
        item_title = re.sub(r'^(?:we need to (?:buy|procure|install|order)|buy|procure|order|supply of)\s+', '', item_title, flags=re.IGNORECASE)

        return ProcurementRequirementItem(
            item=item_title[:120],
            quantity=qty,
            unit=unit,
            specifications=phrase
        )
