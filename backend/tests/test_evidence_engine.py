import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.responses import (
    EvidenceRecord,
    EvidenceType,
    VerificationStatusEnum,
    BisCertificationStatus,
    NormalizedRequirementItem,
    RecommendationResultItem,
    ItemComplianceEvaluation,
    SourcingRecommendationItem,
    ScoreBreakdown,
    LocationModel
)
from backend.app.services.evidence_service import EvidenceService
from backend.app.services.sourcing_service import SourcingService
from backend.app.services.package_evaluation_service import PackageEvaluationService
from backend.app.services.explanation_service import ExplanationService

client = TestClient(app)

# 1. EvidenceRecord Model Validation
def test_evidence_record_validation():
    ev = EvidenceRecord(
        evidence_id="EV-TEST-001",
        evidence_type=EvidenceType.BIS_STANDARD.value,
        title="IS 1786 Standard Specification",
        description="High strength deformed steel bars for concrete reinforcement.",
        source="Bureau of Indian Standards SQLite Database (v5)",
        source_url=None,
        reference_id="IS-1786",
        retrieved_at="2026-09-09",
        verification_status=VerificationStatusEnum.VERIFIED.value,
        supports_claim="IS 1786 applies to high strength deformed TMT steel bars."
    )
    assert ev.evidence_id == "EV-TEST-001"
    assert ev.source_url is None
    assert ev.verification_status == "VERIFIED"
    assert "IS 1786" in ev.supports_claim

# 2. Missing Evidence Handling
def test_missing_evidence_handling():
    evidence_svc = EvidenceService()
    source_empty = {
        "source_id": "SRC-TEST-EMPTY",
        "source_name": "Unverified Metal Trader",
        "source_type": "DISTRIBUTOR",
        "verification_status": "UNVERIFIED",
        "location": {"city": "Unknown", "state": "Unknown"},
        "categories": ["steel"],
        "supported_standards": [],
        "verification_evidence": []
    }
    trust_bd, bis_status = evidence_svc.evaluate_source_trust(source_empty)
    assert bis_status == BisCertificationStatus.NO_EVIDENCE.value
    assert trust_bd.bis_evidence <= 0.20
    assert trust_bd.trust_level == "LOW"

    ev_records = evidence_svc.generate_source_evidence_records(source_empty)
    assert any("NONE" in r.evidence_id for r in ev_records)
    assert any(r.verification_status == "UNVERIFIED" for r in ev_records)

# 3. Stale Evidence / CML Live Verification Notice
def test_stale_evidence_handling():
    evidence_svc = EvidenceService()
    source_cml = {
        "source_id": "SRC-MFR-TEST-CML",
        "source_name": "Test Steel Re-roller",
        "source_type": "MANUFACTURER",
        "verification_status": "VERIFIED",
        "location": {"city": "Bokaro", "state": "Jharkhand", "latitude": 23.66, "longitude": 86.15},
        "categories": ["steel"],
        "supported_standards": ["IS-1786"],
        "verification_evidence": ["Statutory BIS License CML-0009999 for IS 1786 Fe 500D"]
    }
    trust_bd, bis_status = evidence_svc.evaluate_source_trust(source_cml)
    # Never claim live confirmation when only static record is stored
    assert bis_status == BisCertificationStatus.REQUIRES_LIVE_VERIFICATION.value

    ev_records = evidence_svc.generate_source_evidence_records(source_cml)
    cml_rec = next((r for r in ev_records if r.evidence_type == EvidenceType.BIS_LICENSE.value), None)
    assert cml_rec is not None
    assert "Verification required on official BIS portal" in cml_rec.description
    assert cml_rec.reference_id == "CML-0009999"

# 4. Verified Enterprise Evidence Classification
def test_verified_evidence_classification():
    evidence_svc = EvidenceService()
    source_sail = {
        "source_id": "SRC-MFR-SAIL-BOKARO",
        "source_name": "Steel Authority of India Limited (SAIL) - Bokaro Steel Plant",
        "source_type": "MANUFACTURER",
        "verification_status": "VERIFIED",
        "location": {"city": "Bokaro Steel City", "state": "Jharkhand", "latitude": 23.6693, "longitude": 86.1511},
        "categories": ["steel", "rebar"],
        "supported_standards": ["IS-1786", "IS-2062"],
        "verification_evidence": [
            "Statutory BIS License CML-0003042 for IS 1786 Fe 500D",
            "Central Public Sector Undertaking (Govt. of India Enterprise - Maharatna)"
        ]
    }
    trust_bd, bis_status = evidence_svc.evaluate_source_trust(source_sail)
    assert trust_bd.identity_evidence == 1.0
    assert trust_bd.trust_level == "HIGH"
    assert trust_bd.trust_score >= 0.75

    ev_records = evidence_svc.generate_source_evidence_records(source_sail)
    govt_rec = next((r for r in ev_records if r.evidence_type == EvidenceType.GOVERNMENT_RECORD.value), None)
    assert govt_rec is not None
    assert govt_rec.verification_status == "VERIFIED"
    assert "Central Public Sector" in govt_rec.title

# 5. Supplier with No BIS Evidence
def test_supplier_with_no_bis_evidence():
    evidence_svc = EvidenceService()
    distributor = {
        "source_id": "SRC-DIST-NORTH-ELECTRO",
        "source_name": "National Power Cable & Switchgear Distribution Network",
        "source_type": "DISTRIBUTOR",
        "verification_status": "REQUIRES_VENDOR_VERIFICATION",
        "location": {"city": "Gurugram", "state": "Haryana", "latitude": 28.45, "longitude": 77.02},
        "categories": ["cable"],
        "supported_standards": ["IS-694"],
        "verification_evidence": ["Third-party commercial channel entity without primary factory BIS CML license"]
    }
    trust_bd, bis_status = evidence_svc.evaluate_source_trust(distributor)
    assert bis_status == BisCertificationStatus.NO_EVIDENCE.value
    assert trust_bd.trust_score < 0.60

    ev_records = evidence_svc.generate_source_evidence_records(distributor)
    assert any("Vendor verification required" in r.supports_claim for r in ev_records)

# 6. Region-Only Source Evidence Classification
def test_region_only_source_evidence():
    evidence_svc = EvidenceService()
    peenya = {
        "source_id": "SRC-REG-BLR-PEENYA",
        "source_name": "Peenya Industrial Area (KIADB)",
        "source_type": "SOURCING_REGION",
        "verification_status": "REGION_ONLY",
        "location": {"city": "Bengaluru", "state": "Karnataka", "latitude": 13.03, "longitude": 77.51},
        "categories": ["cable", "switchgear"],
        "supported_standards": ["IS-694", "IS-1554-1"],
        "verification_evidence": ["State Industrial Area (KIADB)", "Vendor CML verification required"]
    }
    trust_bd, bis_status = evidence_svc.evaluate_source_trust(peenya)
    assert bis_status == BisCertificationStatus.NOT_APPLICABLE.value
    assert trust_bd.identity_evidence == 0.85

    ev_records = evidence_svc.generate_source_evidence_records(peenya)
    region_notice = next((r for r in ev_records if "Cluster-Level" in r.title), None)
    assert region_notice is not None
    assert "No supplier-level BIS certification evidence attached" in region_notice.description

# 7. Suitability High but Trust Low
def test_suitability_high_but_trust_low():
    sourcing_svc = SourcingService()
    # Unverified source that matches item standard and category perfectly
    unverified_source = {
        "source_id": "SRC-UNVERIFIED-MATCH",
        "source_name": "Unverified Backyard Wire Works",
        "source_type": "MANUFACTURER",
        "verification_status": "UNVERIFIED",
        "location": {"city": "Unknown", "state": "Unknown", "latitude": 0.0, "longitude": 0.0},
        "categories": ["cable"],
        "supported_standards": ["IS-694"],
        "verification_evidence": []
    }
    score_bd = sourcing_svc.calculate_score(
        source=unverified_source,
        item_category="cable",
        item_specs="pvc insulated copper cable per IS 694",
        matching_standard_ids=["IS-694"]
    )
    # Suitability score is high due to category and standard match
    assert score_bd.category_match == 1.0
    assert score_bd.standard_match == 1.0

    trust_bd, bis_status = sourcing_svc.evidence_service.evaluate_source_trust(unverified_source)
    # Trust is low because entity has zero verified credentials
    assert trust_bd.trust_level == "LOW"
    assert trust_bd.trust_score < 0.45
    assert bis_status == BisCertificationStatus.NO_EVIDENCE.value

# 8. Trust High but Suitability Low
def test_trust_high_but_suitability_low():
    sourcing_svc = SourcingService()
    sail_bokaro = sourcing_svc.get_source_by_id("SRC-MFR-SAIL-BOKARO")
    assert sail_bokaro is not None

    # Trust is HIGH for SAIL Bokaro
    trust_bd, bis_status = sourcing_svc.evidence_service.evaluate_source_trust(sail_bokaro)
    assert trust_bd.trust_level == "HIGH"
    assert trust_bd.trust_score >= 0.75

    # But evaluated for an entirely unrelated product domain (e.g. Textile / Fabric)
    score_bd = sourcing_svc.calculate_score(
        source=sail_bokaro,
        item_category="textile",
        item_specs="cotton woven fabric",
        matching_standard_ids=["IS-12345"]
    )
    # Suitability must strictly zero out
    assert score_bd.overall_score == 0.0
    assert score_bd.category_match == 0.0
    assert score_bd.standard_match == 0.0

# 9. READY Decision Condition
def test_ready_decision_condition():
    pkg_svc = PackageEvaluationService()
    norm = NormalizedRequirementItem(
        item_name="Fe 500 TMT Steel Rebars",
        category="Steel",
        quantity=100.0,
        unit="tonnes",
        specifications="High strength Fe 500 deformed bars per IS 1786",
        search_terms=["steel", "rebar"]
    )
    std = RecommendationResultItem(
        standard_id="IS-1786",
        is_code="IS 1786",
        title="High Strength Deformed Steel Bars",
        department="Civil",
        scope_summary="Structural steel",
        key_specifications="Fe 500",
        testing_requirements="Tensile test",
        status="ACTIVE",
        score=0.95,
        reason="Direct match"
    )
    item_eval = ItemComplianceEvaluation(
        item_id="ITEM-01",
        item_name=norm.item_name,
        normalized_profile=norm,
        standards=[std],
        primary_standard=std,
        compliance_status="COMPLIANT",
        score=0.95,
        applicable_scheme="ISI Mark (Scheme I)",
        is_mandatory_certification=True,
        missing_parameters=[],
        evidence=["Governed by IS 1786"],
        recommendation="Ready for procurement"
    )

    # Synthetic verified supplier matching the item
    verified_rec = SourcingRecommendationItem(
        source_id="SRC-MFR-SAIL-BOKARO",
        source_name="SAIL Bokaro Steel Plant",
        source_type="MANUFACTURER",
        verification_status="VERIFIED",
        bis_certification_status="REQUIRES_LIVE_VERIFICATION",
        trust_score=0.88,
        trust_level="HIGH",
        location=LocationModel(city="Bokaro", state="Jharkhand", latitude=23.66, longitude=86.15),
        supported_items=[norm.item_name],
        relevant_standards=["IS-1786"],
        suitability_score=0.92,
        confidence=0.88,
        reasoning=["Verified manufacturer."],
        score_breakdown=ScoreBreakdown(
            category_match=1.0, standard_match=1.0, compliance_evidence=1.0,
            location_relevance=1.0, data_confidence=1.0, overall_score=95.0
        )
    )

    pkg_eval = pkg_svc.evaluate_package([item_eval], sourcing_recs=[verified_rec])
    assert pkg_eval.standards_coverage == 1.0
    assert pkg_eval.sourcing_coverage == 1.0
    # Because live CML portal verification is always required before releasing funds:
    assert pkg_eval.decision_status in ["READY_WITH_VERIFICATION", "READY"]
    assert pkg_eval.decision_summary.can_procure_now is True

# 10. READY_WITH_VERIFICATION Decision Condition
def test_ready_with_verification_decision_condition():
    pkg_svc = PackageEvaluationService()
    norm = NormalizedRequirementItem(
        item_name="1.1 kV XLPE Power Cable",
        category="Cable",
        quantity=500.0,
        unit="meters",
        specifications="Working voltage 1100 V per IS 7098 Part 1",
        search_terms=["cable"]
    )
    std = RecommendationResultItem(
        standard_id="IS-7098-1",
        is_code="IS 7098 (Part 1)",
        title="XLPE Cables",
        department="Electro-technical",
        scope_summary="XLPE Cables",
        key_specifications="1.1 kV",
        testing_requirements="High voltage test",
        status="ACTIVE",
        score=0.90,
        reason="Direct match"
    )
    item_eval = ItemComplianceEvaluation(
        item_id="ITEM-01",
        item_name=norm.item_name,
        normalized_profile=norm,
        standards=[std],
        primary_standard=std,
        compliance_status="COMPLIANT",
        score=0.90,
        applicable_scheme="ISI Mark",
        is_mandatory_certification=True,
        missing_parameters=[],
        evidence=["IS 7098-1"],
        recommendation="Procure"
    )

    # Sourcing from regional industrial cluster (requires buyer vendor check)
    region_rec = SourcingRecommendationItem(
        source_id="SRC-REG-BLR-PEENYA",
        source_name="Peenya Industrial Area",
        source_type="SOURCING_REGION",
        verification_status="REGION_ONLY",
        bis_certification_status="NOT_APPLICABLE",
        trust_score=0.65,
        trust_level="MODERATE",
        location=LocationModel(city="Bengaluru", state="Karnataka", latitude=13.03, longitude=77.51),
        supported_items=[norm.item_name],
        relevant_standards=["IS-7098-1"],
        suitability_score=0.75,
        confidence=0.60,
        reasoning=["Cluster area."],
        score_breakdown=ScoreBreakdown(
            category_match=1.0, standard_match=1.0, compliance_evidence=0.5,
            location_relevance=0.8, data_confidence=0.8, overall_score=75.0
        )
    )

    pkg_eval = pkg_svc.evaluate_package([item_eval], sourcing_recs=[region_rec])
    assert pkg_eval.decision_status == "READY_WITH_VERIFICATION"
    assert pkg_eval.decision_summary.can_procure_now is True
    assert len(pkg_eval.decision_summary.missing_verifications) > 0

# 11. INSUFFICIENT_EVIDENCE Decision Condition
def test_insufficient_evidence_decision_condition():
    pkg_svc = PackageEvaluationService()
    norm1 = NormalizedRequirementItem(
        item_name="Item 1 with Standard",
        category="Steel",
        specifications="Steel bar"
    )
    std1 = RecommendationResultItem(
        standard_id="IS-1786",
        is_code="IS 1786",
        title="Steel",
        department="Civil",
        scope_summary="",
        key_specifications="",
        testing_requirements="",
        status="ACTIVE",
        score=0.80,
        reason=""
    )
    eval1 = ItemComplianceEvaluation(
        item_id="ITEM-01",
        item_name="Item 1",
        normalized_profile=norm1,
        standards=[std1],
        primary_standard=std1,
        compliance_status="COMPLIANT",
        score=0.80,
        applicable_scheme="ISI Mark",
        missing_parameters=[]
    )

    norm2 = NormalizedRequirementItem(
        item_name="Item 2 with No Standard",
        category="Unknown",
        specifications="Custom device"
    )
    eval2 = ItemComplianceEvaluation(
        item_id="ITEM-02",
        item_name="Item 2",
        normalized_profile=norm2,
        standards=[],
        primary_standard=None,
        compliance_status="ACTION_REQUIRED",
        score=0.15,
        applicable_scheme="Voluntary",
        missing_parameters=["Standard not found"]
    )

    # 50% standards coverage -> INSUFFICIENT_EVIDENCE
    pkg_eval = pkg_svc.evaluate_package([eval1, eval2], sourcing_recs=[])
    assert pkg_eval.decision_status in ["INSUFFICIENT_EVIDENCE", "NOT_RECOMMENDED"]
    assert pkg_eval.decision_summary.can_procure_now is False

# 12. NOT_RECOMMENDED Decision Condition
def test_not_recommended_decision_condition():
    pkg_svc = PackageEvaluationService()
    norm = NormalizedRequirementItem(
        item_name="Unknown Unclassifiable Artifact",
        category="Alien",
        specifications="Unidentified physical properties"
    )
    eval_item = ItemComplianceEvaluation(
        item_id="ITEM-01",
        item_name="Unknown Item",
        normalized_profile=norm,
        standards=[],
        primary_standard=None,
        compliance_status="ACTION_REQUIRED",
        score=0.10,
        applicable_scheme="Voluntary",
        missing_parameters=["Item cannot be classified under any Indian Standard"]
    )

    pkg_eval = pkg_svc.evaluate_package([eval_item], sourcing_recs=[])
    assert pkg_eval.decision_status == "NOT_RECOMMENDED"
    assert pkg_eval.decision_summary.can_procure_now is False
    assert pkg_eval.decision_summary.procurement_ready is False

# 13. Gemini with Incomplete Evidence
def test_gemini_with_incomplete_evidence():
    exp_svc = ExplanationService(gemini_api_key=None)
    norm = NormalizedRequirementItem(
        item_name="Incomplete Cable Requirement",
        category="Cable",
        specifications="Wire for electrical hookup"
    )
    eval_item = ItemComplianceEvaluation(
        item_id="ITEM-01",
        item_name="Incomplete Cable",
        normalized_profile=norm,
        standards=[],
        primary_standard=None,
        compliance_status="ACTION_REQUIRED",
        score=0.20,
        applicable_scheme="Voluntary",
        missing_parameters=["Operating voltage rating", "Conductor material"]
    )
    pkg_svc = PackageEvaluationService()
    pkg_eval = pkg_svc.evaluate_package([eval_item], sourcing_recs=[])

    exp = exp_svc.generate_procurement_explanation(
        company="Startup Lab",
        items=[eval_item],
        package_eval=pkg_eval,
        sourcing_recs=[]
    )
    assert exp is not None
    assert len(exp.missing_information) > 0
    assert any("voltage rating" in m for m in exp.missing_information)
    assert any("[REQUIRES VERIFICATION]" in c or "[INFERRED" in c for c in exp.inference_requires_verification + exp.compliance_caveats)

# 14. GET /sources/{source_id}/evidence API Endpoint
def test_source_evidence_api_endpoint():
    res = client.get("/api/v1/procurement/sources/SRC-MFR-SAIL-BOKARO/evidence")
    assert res.status_code == 200
    data = res.json()
    assert data["source_id"] == "SRC-MFR-SAIL-BOKARO"
    assert "SAIL" in data["source_name"]
    assert data["bis_certification_status"] in ["REQUIRES_LIVE_VERIFICATION", "CONFIRMED"]
    assert data["trust_score"] >= 0.70
    assert len(data["evidence"]) >= 3
    # Check that each evidence record has required fields
    for ev in data["evidence"]:
        assert "evidence_id" in ev
        assert "evidence_type" in ev
        assert "title" in ev
        assert "description" in ev
        assert "source" in ev
        assert "verification_status" in ev
        assert "supports_claim" in ev

    # Check 404 for nonexistent source
    res_404 = client.get("/api/v1/procurement/sources/NON_EXISTENT_SOURCE_ID/evidence")
    assert res_404.status_code == 404
