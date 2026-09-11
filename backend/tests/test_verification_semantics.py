import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.sourcing_service import SourcingService
from backend.app.services.evidence_service import EvidenceService
from backend.app.services.explanation_service import ExplanationService
from backend.app.models.responses import (
    SourcingRecommendationItem,
    ScoreBreakdown,
    LocationModel,
    DataProvenanceLabel
)

client = TestClient(app)

def test_static_registry_sources_require_live_verification():
    """
    Guarantees that static evidence (government records, PSU identity, registry records, historical CMLs)
    does NOT produce a current 'CONFIRMED' / 'BUYER_VERIFIED' state.
    All registered manufacturers must require live portal verification.
    """
    sourcing_svc = SourcingService()
    sources = sourcing_svc.get_all_sources()
    
    manufacturers = [s for s in sources if s.get("source_type") == "MANUFACTURER"]
    assert len(manufacturers) >= 5, "Expected registered manufacturers in registry"
    
    for mfr in manufacturers:
        source_id = mfr["source_id"]
        _, bis_status = sourcing_svc.evidence_service.evaluate_source_trust(mfr)
        provenance = sourcing_svc.evidence_service.derive_provenance_label(mfr)
        
        # Static manufacturer data must require live verification (never CONFIRMED)
        assert bis_status in ["REQUIRES_LIVE_VERIFICATION", "EVIDENCE_AVAILABLE"], (
            f"Source {source_id} has static data but evaluated bis_certification_status is '{bis_status}', "
            f"expected 'REQUIRES_LIVE_VERIFICATION' or 'EVIDENCE_AVAILABLE'"
        )
        assert bis_status != "CONFIRMED", f"Source {source_id} produced CONFIRMED from static data!"
        
        # Static manufacturer data must NOT have BUYER_VERIFIED provenance
        assert provenance != "BUYER_VERIFIED", (
            f"Source {source_id} has static provenance '{provenance}', cannot be 'BUYER_VERIFIED'"
        )
        assert provenance in [
            DataProvenanceLabel.GOVERNMENT_RECORD.value,
            DataProvenanceLabel.BIS_EVIDENCE.value,
            DataProvenanceLabel.REGISTRY_EVIDENCE.value
        ]


def test_industrial_corridors_are_strictly_region_only():
    """
    Guarantees that industrial corridor clusters are strictly classified as REGION_ONLY
    and never conflated with verified suppliers or BIS certified entities.
    """
    sourcing_svc = SourcingService()
    sources = sourcing_svc.get_all_sources()
    
    regions = [s for s in sources if s.get("source_type") == "SOURCING_REGION"]
    assert len(regions) >= 10, "Expected industrial corridors in registry"
    
    for r in regions:
        source_id = r["source_id"]
        assert r.get("verification_status") == "REGION_ONLY", f"{source_id} verification_status != REGION_ONLY"
        _, bis_status = sourcing_svc.evidence_service.evaluate_source_trust(r)
        provenance = sourcing_svc.evidence_service.derive_provenance_label(r)
        assert bis_status == "NOT_APPLICABLE", f"{source_id} bis_status != NOT_APPLICABLE"
        assert provenance == DataProvenanceLabel.REGION_ONLY.value


def test_commercial_sources_are_strictly_unverified():
    """
    Guarantees that commercial suppliers and distributors without primary factory CMLs
    remain explicitly unverified.
    """
    sourcing_svc = SourcingService()
    sources = sourcing_svc.get_all_sources()
    
    commercial = [s for s in sources if s.get("source_type") in ["SUPPLIER", "DISTRIBUTOR"]]
    assert len(commercial) >= 1
    
    for comm in commercial:
        source_id = comm["source_id"]
        assert comm.get("verification_status") in ["REQUIRES_VENDOR_VERIFICATION", "UNVERIFIED"]
        _, bis_status = sourcing_svc.evidence_service.evaluate_source_trust(comm)
        provenance = sourcing_svc.evidence_service.derive_provenance_label(comm)
        assert bis_status == "NO_EVIDENCE"
        assert provenance == DataProvenanceLabel.SUPPLIER_DECLARATION.value


def test_static_evidence_records_do_not_produce_confirmed_state():
    """
    Guarantees that evidence records generated from static registry data
    carry verification_method == 'REGISTRY' and verification_status != 'CONFIRMED'.
    """
    evidence_svc = EvidenceService()
    source_psu = {
        "source_id": "SRC-MFR-TEST-PSU",
        "source_name": "National Heavy Electricals",
        "source_type": "MANUFACTURER",
        "verification_status": "VERIFIED",
        "bis_certification_status": "REQUIRES_LIVE_VERIFICATION",
        "provenance_label": "GOVERNMENT_RECORD",
        "location": {"city": "Bhopal", "state": "Madhya Pradesh"},
        "categories": ["electrical", "power"],
        "supported_standards": ["IS-7098-1"],
        "verification_evidence": ["Central Public Sector Enterprise (CPSE) under Ministry of Heavy Industries"]
    }
    
    records = evidence_svc.generate_source_evidence_records(source_psu)
    assert len(records) > 0
    
    for rec in records:
        # Static records must not report CONFIRMED
        assert rec.verification_status != "CONFIRMED", (
            f"Evidence record '{rec.evidence_id}' has status 'CONFIRMED' from static data!"
        )
        assert rec.verification_method in ["REGISTRY", "IMPORTED", "AUTOMATED"]


def test_manual_buyer_verification_is_sole_path_to_confirmed():
    """
    Guarantees that only an explicit manual buyer review transitions a static source
    to CONFIRMED / BUYER_VERIFIED.
    """
    # 1. Source initially requires live verification
    get_resp = client.get("/api/v1/procurement/sources/SRC-MFR-SAIL-BHILAI/verification")
    assert get_resp.status_code == 200
    initial_data = get_resp.json()
    assert initial_data["status"] == "REQUIRES_LIVE_VERIFICATION"
    assert initial_data["verification_method"] == "REGISTRY"
    
    # 2. Submit valid manual buyer review with complete 5-point checklist
    post_payload = {
        "verified_by": "chief.procurement@infrastructure.gov.in",
        "reference_id": "CM/L-0003042",
        "notes": "Verified active license schedule on manakonline.in portal",
        "checklist_confirmed": {
            "license_exists": True,
            "product_category_matches": True,
            "applicable_standard_matches": True,
            "license_currently_valid": True,
            "manufacturer_site_matches": True
        }
    }
    post_resp = client.post("/api/v1/procurement/sources/SRC-MFR-SAIL-BHILAI/verify", json=post_payload)
    assert post_resp.status_code == 200
    updated_data = post_resp.json()
    
    # 3. Explicit manual confirmation recorded
    assert updated_data["status"] == "CONFIRMED"
    assert updated_data["verification_method"] == "MANUAL"
    assert any(
        log["actor"] == "chief.procurement@infrastructure.gov.in" and log["action"] == "MANUAL_VERIFICATION_CONFIRMED"
        for log in updated_data["audit_trail"]
    )


def test_procurement_analyze_endpoint_preserves_semantics():
    """
    Guarantees that POST /api/v1/procurement/analyze produces sourcing recommendations
    with strictly differentiated statuses:
    - Sourcing regions: REGION_ONLY
    - Static manufacturers: REQUIRES_LIVE_VERIFICATION
    - Commercial suppliers: REQUIRES_VENDOR_VERIFICATION
    """
    payload = {
        "company": "Procurement Semantics Verification Corp",
        "requirements": [
            {
                "item": "1.1 kV XLPE insulated electrical cables",
                "quantity": 1000,
                "unit": "meters",
                "specifications": "Crosslinked polyethylene per IS 7098 Part 1"
            },
            {
                "item": "Fe 500D TMT rebar",
                "quantity": 25,
                "unit": "tonnes",
                "specifications": "Reinforcement steel per IS 1786"
            }
        ]
    }
    response = client.post("/api/v1/procurement/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    recs = data["recommendations"]
    assert len(recs) > 0
    
    for r in recs:
        s_type = r.get("sourcing_type")
        v_stat = r.get("verification_status")
        bis_stat = r.get("bis_certification_status")
        p_label = r.get("provenance_label")
        
        if s_type == "SOURCING_REGION":
            assert v_stat == "REGION_ONLY"
            assert bis_stat == "NOT_APPLICABLE"
            assert p_label == "REGION_ONLY"
        elif s_type == "MANUFACTURER":
            if v_stat != "CONFIRMED":
                assert bis_stat == "REQUIRES_LIVE_VERIFICATION"
                assert p_label != "BUYER_VERIFIED"
        elif s_type in ["SUPPLIER", "DISTRIBUTOR"]:
            assert v_stat in ["REQUIRES_VENDOR_VERIFICATION", "UNVERIFIED"]
            assert bis_stat == "NO_EVIDENCE"
            assert p_label == "SUPPLIER_DECLARATION"


def test_explanation_briefing_semantics():
    """
    Guarantees that ExplanationService briefing distinguishes static documented enterprises
    (requiring live verification) from manually confirmed ones.
    """
    explanation_svc = ExplanationService()
    
    # 1. Static manufacturer
    static_item = SourcingRecommendationItem(
        source_id="SRC-MFR-TEST",
        source_name="Static Heavy Forge Ltd",
        source_type="MANUFACTURER",
        location=LocationModel(city="Ranchi", state="Jharkhand", latitude=23.34, longitude=85.30),
        primary_category="steel",
        matched_categories=["steel"],
        relevant_standards=["IS 1786"],
        score=0.88,
        suitability_score=0.90,
        trust_score=0.85,
        confidence=0.85,
        verification_status="REQUIRES_LIVE_VERIFICATION",
        bis_certification_status="REQUIRES_LIVE_VERIFICATION",
        provenance_label=DataProvenanceLabel.GOVERNMENT_RECORD.value,
        score_breakdown=ScoreBreakdown(
            category_match=1.0,
            standard_match=1.0,
            compliance_evidence=0.9,
            location_relevance=0.8,
            data_confidence=0.8,
            overall_score=88.0
        ),
        key_capabilities=["Forged steel manufacturing"],
        reason="Static enterprise test."
    )
    
    from backend.app.models.responses import PackageEvaluation

    package_eval = PackageEvaluation(
        total_items=1,
        item_coverage=1.0,
        compliant_items=1,
        conditional_items=0,
        non_compliant_items=0,
        standards_coverage=1.0,
        sourcing_coverage=1.0,
        verification_coverage=0.0,
        compliance_coverage=1.0,
        evidence_coverage=0.8,
        overall_readiness_score=85,
        readiness_level="HIGH",
        decision_status="READY_WITH_VERIFICATION",
        sourcing_feasibility="FEASIBLE"
    )

    explanation = explanation_svc.generate_procurement_explanation(
        company="Semantics Test Corp",
        items=[],
        package_eval=package_eval,
        sourcing_recs=[static_item]
    )

    supported_joined = " ".join(explanation.supported_by_data)
    caveats_joined = " ".join(explanation.compliance_caveats)

    # Must declare that live verification is required, not claim it is fully verified
    assert "Documented Enterprise (Requires Live Verification)" in supported_joined
    assert "Live operational verification required on official BIS portal (manakonline.in)" in caveats_joined
    assert "Manually Verified Source" not in supported_joined
