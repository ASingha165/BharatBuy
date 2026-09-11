import os
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.app.models.responses import (
    ItemComplianceEvaluation,
    SourcingRecommendationItem,
    LocationModel,
    ScoreBreakdown,
    MapPointItem,
    SourceVerificationResponse
)
from backend.app.models.responses import SearchExpansion, VendorIdentity, CostAssessment
from backend.app.models.requests import ManualVerifyRequest
from backend.app.core.logging import logger
from backend.app.core.config import settings
from backend.app.services.evidence_service import EvidenceService
from backend.app.services.gstin_verification_service import GSTINVerificationService

# Path to the authoritative sourcing registry dataset
DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
SOURCING_REGISTRY_PATH = DATA_DIR / "sourcing-registry-v1.json"

DEFAULT_SCORING_WEIGHTS = {
    "category": 0.25,
    "standard": 0.30,
    "compliance": 0.25,
    "location": 0.10,
    "confidence": 0.10
}

# Verification status baseline evidence scores
COMPLIANCE_EVIDENCE_MAP = {
    "VERIFIED": 1.0,
    "PARTIALLY_VERIFIED": 0.75,
    "REGION_ONLY": 0.50,
    "REQUIRES_VENDOR_VERIFICATION": 0.35,
    "UNVERIFIED": 0.10,
    "UNKNOWN_SOURCE": 0.05
}

# Data confidence based on source provenance
DATA_CONFIDENCE_MAP = {
    "VERIFIED": 0.95,
    "PARTIALLY_VERIFIED": 0.85,
    "REGION_ONLY": 0.80,
    "REQUIRES_VENDOR_VERIFICATION": 0.50,
    "UNVERIFIED": 0.30,
    "UNKNOWN_SOURCE": 0.20
}

class SourcingService:
    """
    Enterprise Sourcing Intelligence Engine (Phase 2 & 3):
    Discovers eligible suppliers, verifies data provenance, computes transparent suitability scores,
    evaluates decoupled source trust, and generates traceable Claim -> Evidence records.

    Strict Zero-Fabrication Rule:
    Never fabricates a supplier. Distinguishes SOURCING_REGION from registered MANUFACTURER / SUPPLIER.
    """

    def __init__(
        self,
        registry_file: Optional[Path] = None,
        weights: Optional[Dict[str, float]] = None,
        evidence_service: Optional[EvidenceService] = None
    ):
        self.registry_path = registry_file or SOURCING_REGISTRY_PATH
        self.weights = weights or dict(DEFAULT_SCORING_WEIGHTS)
        self.evidence_service = evidence_service or EvidenceService()
        self.gstin_service = GSTINVerificationService()
        self.last_search_expansion = SearchExpansion()
        self.sources: List[Dict[str, Any]] = self._load_sourcing_registry()
        logger.info(f"[SOURCING SERVICE] Loaded {len(self.sources)} registered sources and industrial corridors.")

    def _load_sourcing_registry(self) -> List[Dict[str, Any]]:
        from backend.app.core.database import db_manager
        sources: List[Dict[str, Any]] = []

        # Attempt to load from PostgreSQL database if active
        if db_manager.is_postgres:
            try:
                db_sources = db_manager.fetch_all("""
                SELECT source_id, source_name, source_type, verification_status, provenance_label,
                       city, state, latitude, longitude, categories, supported_standards,
                       verification_evidence, description
                FROM sourcing_sources
                WHERE is_demo_data = FALSE
                """)
                if db_sources:
                    for r in db_sources:
                        cat = r["categories"]
                        if isinstance(cat, str):
                            cat = json.loads(cat)
                        stds = r["supported_standards"]
                        if isinstance(stds, str):
                            stds = json.loads(stds)
                        evid = r["verification_evidence"]
                        if isinstance(evid, str):
                            evid = json.loads(evid)

                        item = {
                            "source_id": r["source_id"],
                            "source_name": r["source_name"],
                            "source_type": r["source_type"],
                            "verification_status": r["verification_status"],
                            "location": {
                                "city": r["city"],
                                "state": r["state"],
                                "latitude": float(r["latitude"]),
                                "longitude": float(r["longitude"])
                            },
                            "categories": cat,
                            "supported_standards": stds,
                            "verification_evidence": evid,
                            "description": r["description"]
                        }
                        if r.get("provenance_label"):
                            item["provenance_label"] = r["provenance_label"]
                        sources.append(item)
                    logger.info(f"[SOURCING SERVICE] Loaded {len(sources)} sources from PostgreSQL sourcing_sources table.")
            except Exception as e:
                logger.warning(f"[SOURCING SERVICE] Could not query sourcing_sources from database, falling back to JSON: {e}")

        # Fallback to local JSON registry if database not active or table empty
        if not sources and self.registry_path.exists():
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        sources = list(data)
            except Exception as e:
                logger.error(f"[SOURCING SERVICE] Error reading sourcing registry at {self.registry_path}: {e}")

        if not sources:
            # Fallback embedded baseline data (10 Sourcing Regions + verified Central PSUs)
            sources = [
                {
                    "source_id": "SRC-REG-BLR-PEENYA",
                    "source_name": "Peenya Industrial Area (KIADB)",
                    "source_type": "SOURCING_REGION",
                    "verification_status": "REGION_ONLY",
                    "location": {"city": "Bengaluru", "state": "Karnataka", "latitude": 13.0315, "longitude": 77.5146},
                    "categories": ["cable", "switchgear", "transformer", "electronics", "ups"],
                    "supported_standards": ["IS-694", "IS-1554-1", "IS-7098-1", "IS-2026-1", "IS-16242-1"],
                    "verification_evidence": ["State Industrial Area (KIADB)", "Vendor CML verification required"],
                    "description": "Major South Asian manufacturing cluster hosting licensed BIS manufacturers."
                },
                {
                    "source_id": "SRC-MFR-SAIL-BOKARO",
                    "source_name": "Steel Authority of India Limited (SAIL) - Bokaro Steel Plant",
                    "source_type": "MANUFACTURER",
                    "verification_status": "VERIFIED",
                    "location": {"city": "Bokaro Steel City", "state": "Jharkhand", "latitude": 23.6693, "longitude": 86.1511},
                    "categories": ["steel", "rebar"],
                    "supported_standards": ["IS-1786", "IS-2062"],
                    "verification_evidence": ["BIS License CML-0003042 for IS 1786 Fe 500D/550D", "Central Maharatna PSU"],
                    "description": "Premier central public sector integrated steel plant manufacturing primary TMT rebars."
                }
            ]

        # Phase 5: Demo Mode vs Production Mode Isolation
        if settings.BHARATBUY_DEMO_MODE:
            demo_path = DATA_DIR / "demo-sourcing-registry-v1.json"
            if demo_path.exists():
                try:
                    with open(demo_path, "r", encoding="utf-8") as f:
                        demo_data = json.load(f)
                        if isinstance(demo_data, list):
                            for d in demo_data:
                                d["is_demo_data"] = True
                                d["provenance_label"] = "DEMO_DATA"
                            sources = sources + demo_data
                except Exception as e:
                    logger.error(f"[SOURCING SERVICE] Error loading demo registry: {e}")
        else:
            # Production mode: STRICT ZERO-FABRICATION RULE
            # Filter out any record marked as demo data
            sources = [s for s in sources if not s.get("is_demo_data") and "DEMO" not in s.get("source_id", "").upper()]

        return sources

    def calculate_score(
        self,
        source: Dict[str, Any],
        item_category: str,
        item_specs: str,
        matching_standard_ids: List[str],
        preferred_state: Optional[str] = None
    ) -> ScoreBreakdown:
        """
        Computes transparent multi-factor suitability score components (0-1.0) and overall score (0-100).
        """
        cat_lower = (item_category or "").lower()
        specs_lower = (item_specs or "").lower()
        raw_cats = source.get("categories") or []
        source_cats = [c.lower() for c in raw_cats if isinstance(c, str)]
        raw_stds = source.get("supported_standards") or []
        source_stds = [s for s in raw_stds if isinstance(s, str)]
        v_status = source.get("verification_status", "UNKNOWN_SOURCE")

        # 1. Category Match (0.0 - 1.0)
        category_match = 0.0
        if any(sc in cat_lower or cat_lower in sc for sc in source_cats):
            category_match = 1.0
        elif any(sc in specs_lower for sc in source_cats):
            category_match = 0.70

        # 2. Standard Match (0.0 - 1.0)
        standard_match = 0.0
        exact_std_matches = [s for s in matching_standard_ids if s in source_stds]
        if exact_std_matches:
            standard_match = 1.0
        elif any(any(s.split('-')[1] in std for std in source_stds if '-' in s) for s in matching_standard_ids):
            standard_match = 0.60

        # 3. Compliance Evidence (0.0 - 1.0)
        compliance_evidence = COMPLIANCE_EVIDENCE_MAP.get(v_status, 0.10)

        # 4. Location Relevance (0.0 - 1.0)
        loc_dict = source.get("location") or {}
        source_state = (loc_dict.get("state") or "").lower() if isinstance(loc_dict, dict) else ""
        if preferred_state and preferred_state.lower() in source_state:
            location_relevance = 1.0
        elif source_state in ["karnataka", "gujarat", "maharashtra", "tamil nadu", "delhi ncr", "jharkhand"]:
            location_relevance = 0.85
        else:
            location_relevance = 0.70

        # 5. Data Confidence (0.0 - 1.0)
        data_confidence = DATA_CONFIDENCE_MAP.get(v_status, 0.30)

        # Weighted aggregate score (0 to 100)
        if category_match == 0.0 and standard_match == 0.0:
            # If neither the product domain nor the standard matches, the source is irrelevant
            overall_score = 0.0
        else:
            w = self.weights
            overall_score = (
                category_match * w["category"] +
                standard_match * w["standard"] +
                compliance_evidence * w["compliance"] +
                location_relevance * w["location"] +
                data_confidence * w["confidence"]
            ) * 100.0

        overall_score = round(min(max(overall_score, 0.0), 100.0), 1)

        return ScoreBreakdown(
            category_match=round(category_match, 2),
            standard_match=round(standard_match, 2),
            compliance_evidence=round(compliance_evidence, 2),
            location_relevance=round(location_relevance, 2),
            data_confidence=round(data_confidence, 2),
            overall_score=overall_score
        )

    def generate_recommendations(
        self,
        evaluated_items: List[ItemComplianceEvaluation],
        preferred_state: Optional[str] = None,
        top_k: int = 8,
        buyer_latitude: Optional[float] = None,
        buyer_longitude: Optional[float] = None,
        search_radius_km: Optional[float] = None
    ) -> List[SourcingRecommendationItem]:
        """
        Finds and ranks eligible sources for evaluated procurement items.
        Returns detailed evidence, transparent scoring breakdown, and explicit provenance markers.
        """
        recommendations: List[SourcingRecommendationItem] = []
        matched_pair_keys = set()
        self.last_search_expansion = SearchExpansion(
            requested_radius_km=search_radius_km,
            applied_radius_km=search_radius_km,
            message="Distance filtering was not requested." if buyer_latitude is None or buyer_longitude is None else "Official registry candidates filtered by distance."
        )

        def distance_km(source: Dict[str, Any]) -> Optional[float]:
            if buyer_latitude is None or buyer_longitude is None:
                return None
            loc = source.get("location") or {}
            lat = float(loc.get("latitude", 0.0))
            lon = float(loc.get("longitude", 0.0))
            radius = 6371.0
            d_lat = math.radians(lat - buyer_latitude)
            d_lon = math.radians(lon - buyer_longitude)
            a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(buyer_latitude)) * math.cos(math.radians(lat)) * math.sin(d_lon / 2) ** 2
            return round(radius * 2 * math.asin(math.sqrt(a)), 1)

        def sources_for_item(item: ItemComplianceEvaluation) -> tuple[List[Dict[str, Any]], Optional[float]]:
            if buyer_latitude is None or buyer_longitude is None or not search_radius_km:
                return self.sources, None
            relevant = []
            for source in self.sources:
                d = distance_km(source)
                if d is not None and d <= search_radius_km:
                    relevant.append(source)
            if relevant:
                return relevant, search_radius_km
            expansion_steps = []
            for candidate_radius in [search_radius_km * 2, search_radius_km * 4, 500.0, 2000.0, 5000.0]:
                bounded_radius = min(candidate_radius, 5000.0)
                if bounded_radius > search_radius_km and bounded_radius not in expansion_steps:
                    expansion_steps.append(bounded_radius)
            for expanded_radius in expansion_steps:
                relevant = [s for s in self.sources if (distance_km(s) or float("inf")) <= expanded_radius]
                if relevant:
                    self.last_search_expansion = SearchExpansion(
                        requested_radius_km=search_radius_km,
                        applied_radius_km=expanded_radius,
                        expanded=True,
                        expansion_steps=expansion_steps[:expansion_steps.index(expanded_radius) + 1],
                        message=f"No registry sources found within {search_radius_km:g} km; search expanded to {expanded_radius:g} km."
                    )
                    return relevant, expanded_radius
            self.last_search_expansion = SearchExpansion(
                requested_radius_km=search_radius_km,
                applied_radius_km=None,
                expanded=True,
                expansion_steps=expansion_steps,
                message="No official registry record found within the configured search expansion."
            )
            return [], None

        for item in evaluated_items:
            category_key = item.normalized_profile.category
            specs_key = item.normalized_profile.specifications
            matching_standards_ids = [s.standard_id for s in item.standards]
            if item.primary_standard:
                matching_standards_ids.append(item.primary_standard.standard_id)

            candidate_sources, applied_radius = sources_for_item(item)
            for source in candidate_sources:
                score_bd = self.calculate_score(
                    source=source,
                    item_category=category_key,
                    item_specs=specs_key,
                    matching_standard_ids=matching_standards_ids,
                    preferred_state=preferred_state
                )

                # Filter out sources that have neither category nor standard relevance
                if score_bd.category_match == 0.0 and score_bd.standard_match == 0.0:
                    continue

                source_id = source["source_id"]
                rec_pair_key = f"{source_id}_{item.item_id}"
                if rec_pair_key in matched_pair_keys:
                    continue
                matched_pair_keys.add(rec_pair_key)

                loc_data = source["location"]
                loc_model = LocationModel(
                    city=loc_data["city"],
                    state=loc_data["state"],
                    latitude=float(loc_data["latitude"]),
                    longitude=float(loc_data["longitude"])
                )

                # Format human-readable reasoning and BIS relevance
                reasoning: List[str] = []
                bis_relevance: List[str] = []
                st_type = source["source_type"]
                v_stat = source["verification_status"]

                if st_type == "MANUFACTURER":
                    reasoning.append(
                        f"Manufacturer (Requires Live Verification): {source['source_name']} operates statutory licensed production for {category_key}. Live validity audit on official BIS portal required."
                    )
                    bis_relevance.extend(source.get("supported_standards", []))
                elif st_type == "SOURCING_REGION":
                    reasoning.append(
                        f"Sourcing Region: {source['source_name']} is an active industrial corridor with licensed manufacturing capacity for {category_key}."
                    )
                    reasoning.append("Regional opportunity: Independent buyer audit of vendor BIS CML is recommended prior to buyer approval.")
                elif v_stat == "REQUIRES_VENDOR_VERIFICATION":
                    reasoning.append(
                        f"Channel Distributor: {source['source_name']} provides stocking distribution; original mill test certificate and manufacturer BIS license required."
                    )
                else:
                    reasoning.append(f"{source['source_name']} matched on technical capability for {category_key}.")

                suitability_norm = round(score_bd.overall_score / 100.0, 4)
                confidence_norm = round(suitability_norm * score_bd.data_confidence, 4)

                trust_bd, bis_status = self.evidence_service.evaluate_source_trust(source)
                ev_records = self.evidence_service.generate_source_evidence_records(
                    source=source,
                    item_name=item.item_name,
                    matching_standards=item.standards
                )
                prov_label = self.evidence_service.derive_provenance_label(source)
                is_demo = bool(source.get("is_demo_data") or "DEMO" in source_id.upper())
                gstin_result = self.gstin_service.verify_authoritatively(source.get("gstin"))
                source_distance = distance_km(source)
                official_status = "NOT_APPLICABLE_REGION" if st_type == "SOURCING_REGION" else (
                    "DOCUMENTED_OFFICIAL_RECORD" if prov_label in ["GOVERNMENT_RECORD", "BIS_EVIDENCE", "AUTHORITATIVE"] else "UNVERIFIED"
                )

                item_rec = SourcingRecommendationItem(
                    source_id=source_id,
                    source_name=source["source_name"],
                    source_type=st_type,
                    verification_status=v_stat,
                    bis_certification_status=bis_status,
                    provenance_label=prov_label,
                    is_demo_data=is_demo,
                    trust_score=trust_bd.trust_score,
                    trust_level=trust_bd.trust_level,
                    trust_breakdown=trust_bd,
                    evidence_records=ev_records,
                    verification_evidence=source.get("verification_evidence", []),
                    location=loc_model,
                    supported_items=[item.item_name],
                    relevant_standards=source.get("supported_standards", []),
                    bis_relevance=bis_relevance if bis_relevance else source.get("supported_standards", []),
                    suitability_score=suitability_norm,
                    confidence=confidence_norm,
                    reasoning=reasoning,
                    score_breakdown=score_bd,
                    vendor_identity=VendorIdentity(
                        vendor_id=source_id if st_type != "SOURCING_REGION" else None,
                        legal_name=source.get("source_name") if st_type != "SOURCING_REGION" else None,
                        gstin_verification=gstin_result,
                        registration_status="UNKNOWN" if st_type != "SOURCING_REGION" else "NOT_APPLICABLE",
                        provenance=prov_label
                    ),
                    official_record_status=official_status,
                    official_record_source="BharatBuy registry with documented provenance; GST registration not authoritatively verified",
                    distance_from_buyer_km=source_distance,
                    range_status="WITHIN_RANGE" if source_distance is not None and applied_radius is not None and source_distance <= applied_radius else ("DISTANCE_UNKNOWN" if source_distance is None else "OUTSIDE_RANGE"),
                    cost_assessment=CostAssessment()
                )
                recommendations.append(item_rec)

        # Fallback if zero items matched
        if not recommendations and self.sources and buyer_latitude is None:
            primary_src = self.sources[0]
            loc_data = primary_src["location"]
            loc_model = LocationModel(
                city=loc_data["city"],
                state=loc_data["state"],
                latitude=float(loc_data["latitude"]),
                longitude=float(loc_data["longitude"])
            )
            fallback_bd = ScoreBreakdown(
                category_match=0.5,
                standard_match=0.3,
                compliance_evidence=0.5,
                location_relevance=0.7,
                data_confidence=0.8,
                overall_score=55.0
            )
            fb_trust_bd, fb_bis_status = self.evidence_service.evaluate_source_trust(primary_src)
            fb_ev_records = self.evidence_service.generate_source_evidence_records(primary_src)
            fb_prov_label = self.evidence_service.derive_provenance_label(primary_src)
            fb_is_demo = bool(primary_src.get("is_demo_data") or "DEMO" in primary_src["source_id"].upper())

            recommendations.append(SourcingRecommendationItem(
                source_id=primary_src["source_id"],
                source_name=primary_src["source_name"],
                source_type=primary_src["source_type"],
                verification_status=primary_src["verification_status"],
                bis_certification_status=fb_bis_status,
                provenance_label=fb_prov_label,
                is_demo_data=fb_is_demo,
                trust_score=fb_trust_bd.trust_score,
                trust_level=fb_trust_bd.trust_level,
                trust_breakdown=fb_trust_bd,
                evidence_records=fb_ev_records,
                verification_evidence=primary_src.get("verification_evidence", []),
                location=loc_model,
                supported_items=[i.item_name for i in evaluated_items],
                relevant_standards=primary_src.get("supported_standards", []),
                bis_relevance=primary_src.get("supported_standards", []),
                suitability_score=0.55,
                confidence=0.44,
                reasoning=["Fallback regional industrial corridor capable of custom procurement sourcing."],
                    score_breakdown=fallback_bd,
                    official_record_status="NOT_APPLICABLE_REGION" if primary_src.get("source_type") == "SOURCING_REGION" else "UNVERIFIED",
                    official_record_source="BharatBuy registry fallback; no authoritative vendor verification",
                    vendor_identity=VendorIdentity(
                        vendor_id=None if primary_src.get("source_type") == "SOURCING_REGION" else primary_src.get("source_id"),
                        legal_name=None if primary_src.get("source_type") == "SOURCING_REGION" else primary_src.get("source_name"),
                        registration_status="NOT_APPLICABLE" if primary_src.get("source_type") == "SOURCING_REGION" else "UNKNOWN",
                        provenance=fb_prov_label
                    ),
                    cost_assessment=CostAssessment()
            ))

        # Rank descending by overall score
        recommendations.sort(key=lambda x: x.suitability_score, reverse=True)
        return recommendations[:top_k]

    def build_map_points(
        self,
        recommendations: List[SourcingRecommendationItem]
    ) -> List[MapPointItem]:
        """
        Builds semantic map points for Leaflet visualization with unique geographic markers.
        """
        points: List[MapPointItem] = []
        seen_coordinates = set()

        for rec in recommendations:
            coord_key = f"{rec.location.latitude:.4f}_{rec.location.longitude:.4f}"
            if coord_key not in seen_coordinates:
                seen_coordinates.add(coord_key)
                points.append(MapPointItem(
                    id=rec.source_id,
                    title=rec.source_name,
                    location=f"{rec.location.city}, {rec.location.state}",
                    latitude=rec.location.latitude,
                    longitude=rec.location.longitude,
                    source_type=rec.source_type,
                    verification_status=rec.verification_status,
                    provenance_label=rec.provenance_label,
                    is_demo_data=rec.is_demo_data,
                    categories=rec.supported_items,
                    supported_items=rec.supported_items,
                    relevant_standards=rec.relevant_standards,
                    suitability_score=rec.suitability_score,
                    evidence_preview=rec.verification_evidence[:2]
                    ,distance_from_buyer_km=rec.distance_from_buyer_km
                    ,range_status=rec.range_status
                    ,official_record_status=rec.official_record_status
                ))

        return points

    def get_all_sources(
        self,
        category: Optional[str] = None,
        standard_id: Optional[str] = None,
        verification_status: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Queries the sourcing registry with optional filters.
        """
        results = self.sources
        if category:
            cat_q = category.lower()
            results = [s for s in results if any(cat_q in c.lower() for c in s.get("categories", []))]
        if standard_id:
            std_q = standard_id.upper()
            results = [s for s in results if any(std_q in st.upper() for st in s.get("supported_standards", []))]
        if verification_status:
            v_q = verification_status.upper()
            results = [s for s in results if s.get("verification_status", "").upper() == v_q]
        if source_type:
            st_q = source_type.upper()
            results = [s for s in results if s.get("source_type", "").upper() == st_q]
        return results

    def get_source_by_id(self, source_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single sourcing entity by ID.
        """
        for s in self.sources:
            if s.get("source_id", "").upper() == source_id.upper():
                return s
        return None

    def get_source_evidence(self, source_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves evidence records, trust evaluation, and provenance chain for a single source.
        """
        source = self.get_source_by_id(source_id)
        if not source:
            return None
        trust_bd, bis_status = self.evidence_service.evaluate_source_trust(source)
        evidence = self.evidence_service.generate_source_evidence_records(source)
        provenance_chain = self.evidence_service.generate_provenance_chain(source)
        prov_label = self.evidence_service.derive_provenance_label(source)
        is_demo = bool(source.get("is_demo_data") or "DEMO" in source.get("source_id", "").upper())
        return {
            "source_id": source.get("source_id"),
            "source_name": source.get("source_name"),
            "source_type": source.get("source_type"),
            "verification_status": source.get("verification_status"),
            "bis_certification_status": bis_status,
            "provenance_label": prov_label,
            "is_demo_data": is_demo,
            "trust_score": trust_bd.trust_score,
            "trust_level": trust_bd.trust_level,
            "evidence": evidence,
            "provenance_chain": provenance_chain
        }

    def get_source_verification(self, source_id: str) -> Optional[SourceVerificationResponse]:
        """
        Retrieves structured verification status, workflow instructions, and audit trail.
        """
        source = self.get_source_by_id(source_id)
        if not source:
            return None
        return self.evidence_service.get_source_verification_details(source_id, source)

    def verify_source_manually(self, source_id: str, request: ManualVerifyRequest) -> Optional[SourceVerificationResponse]:
        """
        Records an explicit buyer manual verification on official BIS portal.
        """
        source = self.get_source_by_id(source_id)
        if not source:
            return None
        return self.evidence_service.record_manual_verification(source_id, source, request)

