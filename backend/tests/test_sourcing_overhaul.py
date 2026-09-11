from backend.app.models.requests import ProcurementAnalysisRequest, ProcurementRequirementItem
from backend.app.models.responses import (
    ItemComplianceEvaluation,
    NormalizedRequirementItem,
    RecommendationResultItem,
)
from backend.app.services.gstin_verification_service import GSTINVerificationService
from backend.app.services.sourcing_service import SourcingService


def test_gstin_format_does_not_claim_authoritative_verification():
    service = GSTINVerificationService()

    result = service.verify("27AAPFU0939F1ZV")

    assert result.status in {"VERIFICATION_UNAVAILABLE", "GSTIN_INVALID"}
    assert result.status != "VERIFIED"
    assert result.verification_source != "GOVERNMENT_API"


def test_procurement_request_supports_location_radius_and_budget():
    request = ProcurementAnalysisRequest(
        company="Example Buyer",
        requirements=[ProcurementRequirementItem(item="Electrical cable")],
        buyer_latitude=28.6139,
        buyer_longitude=77.2090,
        search_radius_km=100,
        budget_amount=100000,
        budget_tolerance_pct=10,
    )

    assert request.search_radius_km == 100
    assert request.budget_amount == 100000


def test_sourcing_filter_expands_without_fabricating_fallback():
    service = SourcingService()
    service.sources = [{
        "source_id": "SRC-TEST-CABLE",
        "source_name": "Documented Cable Record",
        "source_type": "MANUFACTURER",
        "verification_status": "PARTIALLY_VERIFIED",
        "location": {"city": "Bengaluru", "state": "Karnataka", "latitude": 13.03, "longitude": 77.51},
        "categories": ["cable"],
        "supported_standards": ["IS-7098-1"],
        "verification_evidence": ["Registry record; live verification required"],
    }]
    normalized = NormalizedRequirementItem(
        item_name="Electrical cable",
        category="cable",
        specifications="1.1 kV XLPE cable",
    )
    standard = RecommendationResultItem(
        standard_id="IS-7098-1",
        is_code="IS 7098 (Part 1)",
        title="Cable standard",
        department="Electro-technical",
        scope_summary="Cable scope",
        key_specifications="1.1 kV",
        testing_requirements="Electrical tests",
        status="ACTIVE",
        score=0.8,
        reason="Technical match",
    )
    item = ItemComplianceEvaluation(
        item_id="ITEM-01",
        item_name="Electrical cable",
        normalized_profile=normalized,
        standards=[standard],
        primary_standard=standard,
        compliance_status="COMPLIANT",
        score=0.8,
        evidence=[],
    )

    recommendations = service.generate_recommendations(
        [item], buyer_latitude=28.61, buyer_longitude=77.20, search_radius_km=50
    )

    assert recommendations
    assert recommendations[0].distance_from_buyer_km is not None
    assert recommendations[0].range_status == "WITHIN_RANGE"
    assert service.last_search_expansion.expanded is True
    assert recommendations[0].vendor_identity.gstin_verification.status == "UNVERIFIED"
    assert recommendations[0].cost_assessment.status == "COST_UNKNOWN"
