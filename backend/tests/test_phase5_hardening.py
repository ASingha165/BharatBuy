import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.config import settings
from backend.app.services.sourcing_service import SourcingService
from backend.app.services.evidence_service import derive_provenance_label, EvidenceService
from backend.app.services.package_evaluation_service import PackageEvaluationService
from backend.app.services.explanation_service import ExplanationService
from backend.app.models.responses import (
    ItemComplianceEvaluation,
    RecommendationResultItem,
    SourcingRecommendationItem,
    DecisionSummary,
    DataProvenanceLabel,
    NormalizedRequirementItem
)

client = TestClient(app)

# 1. Demo Mode Disabled by Default (Production Integrity)
def test_demo_mode_disabled_by_default():
    sourcing_svc = SourcingService()
    sources = sourcing_svc.get_all_sources()
    
    # Must contain ONLY authentic sources (17 records)
    assert len(sources) == 17
    # Zero demo entities in production registry
    assert not any(s.get("is_demo_data") is True for s in sources)
    assert not any("DEMO" in s.get("source_id", "") for s in sources)
    assert not any(s.get("provenance_label") == "DEMO_DATA" for s in sources)

# 2. Demo Mode Enabled Loads Isolated Demo Sources
def test_demo_mode_enabled_loads_isolated_registry(monkeypatch):
    monkeypatch.setattr(settings, "BHARATBUY_DEMO_MODE", True)
    
    demo_sourcing_svc = SourcingService()
    sources = demo_sourcing_svc.get_all_sources()
    
    # Must include authentic sources + isolated demo sources (17 + 3 = 20)
    assert len(sources) == 20
    demo_sources = [s for s in sources if s.get("is_demo_data") is True]
    assert len(demo_sources) == 3
    for ds in demo_sources:
        assert ds.get("is_demo_data") is True
        assert ds.get("provenance_label") == "DEMO_DATA"
        assert "SRC-DEMO" in ds.get("source_id")

# 3. Synthetic Mock Data Isolation Audit
def test_synthetic_mock_data_isolation():
    sourcing_svc = SourcingService()
    sources = sourcing_svc.get_all_sources()
    
    for s in sources:
        # Check that no synthetic tester or mock auditor is pre-verified in production
        evidence_list = s.get("verification_evidence", [])
        assert not any("qa_auditor@startup.org" in str(ev) for ev in evidence_list)
        assert not any("mock_auditor" in str(ev).lower() for ev in evidence_list)
        
        # Verify that manufacturers in production are authentic entities
        if s.get("source_type") == "MANUFACTURER":
            assert s.get("source_id") in [
                "SRC-MFR-SAIL-BOKARO",
                "SRC-MFR-SAIL-BHILAI",
                "SRC-MFR-BHEL-BHOPAL",
                "SRC-MFR-CEL-SAHIBABAD",
                "SRC-MFR-CCI-TANDUR",
                "SRC-MFR-ITI-BENGALURU"
            ]

# 4. Strict Provenance Label Assignment
def test_provenance_label_assignment():
    # SOURCING_REGION -> REGION_ONLY
    region_source = {"source_type": "SOURCING_REGION", "verification_status": "REGION_ONLY"}
    assert derive_provenance_label(region_source) == "REGION_ONLY"
    
    # Demo Source -> DEMO_DATA
    demo_source = {"is_demo_data": True, "source_id": "SRC-DEMO-TEST"}
    assert derive_provenance_label(demo_source) == "DEMO_DATA"
    
    # PSU Gazette / Government Record
    psu_source = {
        "source_type": "MANUFACTURER",
        "verification_evidence": ["Central Public Sector Enterprise (CPSE) under Ministry of Steel; Gazette notification"]
    }
    assert derive_provenance_label(psu_source) == "GOVERNMENT_RECORD"
    
    # Confirmed Live Buyer Verification
    confirmed_source = {"bis_certification_status": "CONFIRMED"}
    assert derive_provenance_label(confirmed_source) == "BUYER_VERIFIED"
    
    # Verified BIS CML License
    bis_source = {
        "source_type": "MANUFACTURER",
        "verification_evidence": ["BIS CML License No. CM/L-0254128 valid under Bureau of Indian Standards"]
    }
    assert derive_provenance_label(bis_source) == "BIS_EVIDENCE"
    
    # Commercial Distributor / Supplier
    supplier_source = {"source_type": "SUPPLIER", "verification_status": "REQUIRES_VENDOR_VERIFICATION"}
    assert derive_provenance_label(supplier_source) == "SUPPLIER_DECLARATION"

# 5. Procurement Decision Semantics Hardening & String Exactness
def test_procurement_decision_semantics_hardening():
    eval_svc = PackageEvaluationService()
    
    std = RecommendationResultItem(
        standard_id="IS-1786",
        is_code="IS 1786",
        title="High strength deformed steel bars and wires for concrete reinforcement",
        department="Civil Engineering",
        scope_summary="Specification for high strength deformed steel bars",
        key_specifications="Fe 500 grade, yield strength 500 MPa",
        testing_requirements="Tensile test, bend test, rebend test",
        publication_year=2008,
        status="ACTIVE",
        score=0.92,
        reason="Direct product match",
        related_standards=[]
    )
    
    profile = NormalizedRequirementItem(
        item_name="TMT Steel Bars",
        category="steel",
        quantity=50,
        unit="MT",
        specifications="Fe 500 grade TMT rebar",
        mandatory_certifications=["ISI Mark"],
        inferred_standard_requirements=["IS 1786"],
        search_terms=["steel", "rebar"]
    )
    
    item_eval = ItemComplianceEvaluation(
        item_id="ITEM-01",
        item_name="TMT Steel Bars",
        normalized_profile=profile,
        standards=[std],
        primary_standard=std,
        compliance_status="COMPLIANT",
        score=0.92,
        applicable_scheme="ISI Mark Scheme",
        is_mandatory_certification=True,
        missing_parameters=[],
        evidence=["Tested per IS 1786 clauses."],
        recommendation="Procure with ISI mark."
    )
    
    # Case A: READY_WITH_VERIFICATION (pending live portal audit)
    unconfirmed_rec = SourcingRecommendationItem(
        source_id="SRC-SAIL-BOKARO",
        source_name="SAIL Bokaro Steel Plant",
        source_type="MANUFACTURER",
        verification_status="VERIFIED",
        bis_certification_status="REQUIRES_LIVE_VERIFICATION",
        trust_score=0.90,
        trust_level="HIGH",
        provenance_label="GOVERNMENT_RECORD",
        location={"city": "Bokaro", "state": "Jharkhand", "latitude": 23.6693, "longitude": 86.1511},
        supported_items=["TMT Steel Bars"],
        relevant_standards=["IS 1786"],
        suitability_score=0.88,
        confidence=0.90,
        verification_evidence=["CPSE Gazette disclosure"]
    )
    
    pkg_verif = eval_svc.evaluate_package([item_eval], [unconfirmed_rec])
    assert pkg_verif.decision_status == "READY_WITH_VERIFICATION"
    assert pkg_verif.decision_summary.can_procure_now is True
    assert pkg_verif.decision_summary.procurement_ready is False
    assert pkg_verif.decision_summary.summary_text == (
        "Package Decision: READY WITH VERIFICATION. Suitable sourcing identified; verification required before buyer approval."
    )
    
    # Case B: READY (confirmed live by buyer on portal)
    confirmed_rec = SourcingRecommendationItem(
        source_id="SRC-SAIL-BOKARO",
        source_name="SAIL Bokaro Steel Plant",
        source_type="MANUFACTURER",
        verification_status="VERIFIED",
        bis_certification_status="CONFIRMED",
        trust_score=0.95,
        trust_level="HIGH",
        provenance_label="BUYER_VERIFIED",
        location={"city": "Bokaro", "state": "Jharkhand", "latitude": 23.6693, "longitude": 86.1511},
        supported_items=["TMT Steel Bars"],
        relevant_standards=["IS 1786"],
        suitability_score=0.92,
        confidence=0.95,
        verification_evidence=["CPSE Gazette disclosure", "Confirmed on manakonline.in"]
    )
    
    pkg_ready = eval_svc.evaluate_package([item_eval], [confirmed_rec])
    assert pkg_ready.decision_status == "READY"
    assert pkg_ready.decision_summary.can_procure_now is True
    assert pkg_ready.decision_summary.procurement_ready is True
    assert pkg_ready.decision_summary.summary_text == (
        "Package Decision: READY. Procurement-ready for buyer approval. All mandatory standards identified and verified sourcing established."
    )
    
    # Case C: INSUFFICIENT_EVIDENCE (One item mapped to sourcing, another item lacks sourcing)
    cable_profile = NormalizedRequirementItem(
        item_name="Specialty Sensor Cable",
        category="cable",
        quantity=200,
        unit="meters",
        specifications="High temperature sensor wire",
        mandatory_certifications=[],
        inferred_standard_requirements=[],
        search_terms=["sensor", "wire"]
    )
    cable_item = ItemComplianceEvaluation(
        item_id="ITEM-02",
        item_name="Specialty Sensor Cable",
        normalized_profile=cable_profile,
        standards=[std],
        primary_standard=std,
        compliance_status="COMPLIANT",
        score=0.75,
        applicable_scheme="Voluntary",
        is_mandatory_certification=False,
        missing_parameters=[],
        evidence=[],
        recommendation="Procure"
    )
    # unconfirmed_rec supports only "TMT Steel Bars", so "Specialty Sensor Cable" has no sourcing (sourcing_cov = 0.50)
    pkg_insufficient = eval_svc.evaluate_package([item_eval, cable_item], [unconfirmed_rec])
    assert pkg_insufficient.decision_status == "INSUFFICIENT_EVIDENCE"
    assert pkg_insufficient.decision_summary.can_procure_now is False
    assert pkg_insufficient.decision_summary.procurement_ready is False
    assert pkg_insufficient.decision_summary.summary_text == (
        "Package Decision: INSUFFICIENT EVIDENCE. Evidence insufficient for confident sourcing recommendation. Resolve pending specifications or sourcing gaps."
    )
    
    # Case D: NOT_RECOMMENDED
    non_compliant_item = ItemComplianceEvaluation(
        item_id="ITEM-03",
        item_name="Unknown Material",
        normalized_profile=profile,
        standards=[],
        primary_standard=None,
        compliance_status="ACTION_REQUIRED",
        score=0.10,
        applicable_scheme="UNKNOWN",
        is_mandatory_certification=False,
        missing_parameters=["Standard IS code", "Grade"],
        evidence=[],
        recommendation="Action required"
    )
    pkg_not_rec = eval_svc.evaluate_package([non_compliant_item], [])
    assert pkg_not_rec.decision_status == "NOT_RECOMMENDED"
    assert pkg_not_rec.decision_summary.can_procure_now is False
    assert pkg_not_rec.decision_summary.procurement_ready is False
    assert pkg_not_rec.decision_summary.summary_text == (
        "Package Decision: NOT RECOMMENDED. No sufficiently suitable sourcing exists or mandatory compliance requirements cannot be satisfied."
    )

# 6. Repository-Wide Elimination of Forbidden Autonomous PO Release Phrases
def test_forbidden_phrases_eliminated():
    eval_svc = PackageEvaluationService()
    
    # Generate multiple package evaluations
    pkgs = [
        eval_svc.evaluate_package([]),
    ]
    
    forbidden_phrases = [
        "immediate po release permitted",
        "po approved",
        "purchase authorized",
        "no verification needed",
        "directly procurement-ready without buyer review",
        "autonomous purchase release",
        "po automatically approved"
    ]
    
    for pkg in pkgs:
        summary_lower = pkg.decision_summary.summary_text.lower()
        for phrase in forbidden_phrases:
            assert phrase not in summary_lower, f"Forbidden phrase '{phrase}' found in: {pkg.decision_summary.summary_text}"

# 7. Grounded Explanation Deterministic Fallback Notice
def test_explanation_deterministic_fallback_notice():
    exp_svc = ExplanationService(gemini_api_key=None)
    
    # Test single standard explanation fallback
    single_exp = exp_svc.generate_explanation(
        query="cables",
        features={"voltage": "1.1 kV"},
        recommendations=[{"is_code": "IS 694", "title": "PVC Cables", "score": 0.8, "reason": "Test"}]
    )
    assert "Gemini explanation unavailable. The recommendation below is based on retrieved standards and registered source evidence." in single_exp
    
    # Test package explanation fallback
    eval_svc = PackageEvaluationService()
    pkg_eval = eval_svc.evaluate_package([])
    pkg_exp = exp_svc.generate_procurement_explanation(
        company="SolarTech Labs",
        items=[],
        package_eval=pkg_eval,
        sourcing_recs=[]
    )
    assert "Gemini explanation" in pkg_exp.summary
    assert "unavailable" in pkg_exp.summary
    assert "retrieved standards and registered source evidence" in pkg_exp.summary
    assert "SolarTech Labs" in pkg_exp.summary
    assert "SolarTech Labs" in pkg_exp.summary

# 8. 5-Metric Package Coverage Calculations
def test_5_metric_package_coverage():
    eval_svc = PackageEvaluationService()
    
    std = RecommendationResultItem(
        standard_id="IS-1786",
        is_code="IS 1786",
        title="High strength deformed steel bars",
        department="Civil Engineering",
        scope_summary="Specification for steel bars",
        key_specifications="Fe 500",
        testing_requirements="Tensile test",
        publication_year=2008,
        status="ACTIVE",
        score=0.90,
        reason="Match",
        related_standards=[]
    )
    profile = NormalizedRequirementItem(
        item_name="TMT Steel",
        category="steel",
        quantity=10,
        unit="MT",
        specifications="Fe 500",
        mandatory_certifications=["ISI Mark"],
        inferred_standard_requirements=["IS 1786"],
        search_terms=["steel"]
    )
    item = ItemComplianceEvaluation(
        item_id="ITEM-01",
        item_name="TMT Steel",
        normalized_profile=profile,
        standards=[std],
        primary_standard=std,
        compliance_status="COMPLIANT",
        score=0.90,
        applicable_scheme="ISI Mark Scheme",
        is_mandatory_certification=True,
        missing_parameters=[],
        evidence=[],
        recommendation="Procure"
    )
    rec = SourcingRecommendationItem(
        source_id="SRC-SAIL-BOKARO",
        source_name="SAIL Bokaro",
        source_type="MANUFACTURER",
        verification_status="VERIFIED",
        bis_certification_status="REQUIRES_LIVE_VERIFICATION",
        provenance_label="GOVERNMENT_RECORD",
        location={"city": "Bokaro", "state": "Jharkhand", "latitude": 23.6, "longitude": 86.1},
        supported_items=["TMT Steel"],
        relevant_standards=["IS 1786"],
        suitability_score=0.9,
        confidence=0.9
    )
    
    pkg = eval_svc.evaluate_package([item], [rec])
    
    assert 0.0 <= pkg.standards_coverage <= 1.0
    assert 0.0 <= pkg.compliance_coverage <= 1.0
    assert 0.0 <= pkg.sourcing_coverage <= 1.0
    assert 0.0 <= pkg.evidence_coverage <= 1.0
    assert 0.0 <= pkg.verification_coverage <= 1.0
    assert pkg.standards_coverage == 1.0
    assert pkg.compliance_coverage == 1.0
    assert pkg.sourcing_coverage == 1.0
    assert pkg.evidence_coverage == 1.0
    assert pkg.verification_coverage == 1.0

# 9. Health Endpoint returns is_demo_mode
def test_health_endpoint_returns_demo_mode():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "is_demo_mode" in data
    assert isinstance(data["is_demo_mode"], bool)

# 10. Procurement Analyze API Error Handling
def test_procurement_analyze_validation_errors():
    # Empty company rejected with 422 (Pydantic validation) or 400
    res_empty_company = client.post("/api/v1/procurement/analyze", json={
        "company": "",
        "requirements": [{"item": "cable"}]
    })
    assert res_empty_company.status_code in [400, 422]

    # Whitespace company rejected with 400 by route handler
    res_ws_company = client.post("/api/v1/procurement/analyze", json={
        "company": "   ",
        "requirements": [{"item": "cable"}]
    })
    assert res_ws_company.status_code == 400
    assert "Company name cannot be empty" in res_ws_company.json()["detail"]
    
    # Empty requirements and description
    res_empty_reqs = client.post("/api/v1/procurement/analyze", json={
        "company": "Test Co",
        "requirements": [],
        "description": ""
    })
    assert res_empty_reqs.status_code == 400
    assert "Either 'requirements' list or a natural-language 'description'" in res_empty_reqs.json()["detail"]
