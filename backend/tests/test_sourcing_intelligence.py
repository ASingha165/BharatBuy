import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.requests import ProcurementRequirementItem, ProcurementAnalysisRequest
from backend.app.models.responses import NormalizedRequirementItem, RecommendationResultItem, ItemComplianceEvaluation
from backend.app.services.sourcing_service import SourcingService
from backend.app.services.package_evaluation_service import PackageEvaluationService
from backend.app.services.explanation_service import ExplanationService

client = TestClient(app)

# 1. Verified Supplier Test
def test_verified_supplier_matching():
    sourcing_svc = SourcingService()
    norm = NormalizedRequirementItem(
        item_name="Fe 500 High strength deformed TMT steel bars",
        category="Steel",
        quantity=50.0,
        unit="tonnes",
        specifications="Yield strength 500 MPa per IS 1786",
        mandatory_certifications=["ISI Mark"],
        inferred_standard_requirements=["IS-1786"],
        search_terms=["steel", "rebar", "is 1786"]
    )
    matching_std = RecommendationResultItem(
        standard_id="IS-1786",
        is_code="IS 1786",
        title="High Strength Deformed Steel Bars and Wires for Concrete Reinforcement",
        department="Civil",
        scope_summary="Covers physical and chemical requirements for Fe 500 steel rebars.",
        key_specifications="Yield strength >= 500 N/mm2, Elongation >= 14.5%",
        testing_requirements="Tensile test, Bend test, Rebend test",
        status="ACTIVE",
        score=0.92,
        reason="Direct match for Fe 500 TMT steel rebar."
    )
    item_eval = ItemComplianceEvaluation(
        item_id="ITEM-01",
        item_name=norm.item_name,
        normalized_profile=norm,
        standards=[matching_std],
        primary_standard=matching_std,
        compliance_status="COMPLIANT",
        score=0.92,
        applicable_scheme="ISI Mark (Scheme I)",
        is_mandatory_certification=True,
        missing_parameters=[],
        evidence=["Governed by IS 1786"],
        recommendation="Procure from verified manufacturer"
    )

    recs = sourcing_svc.generate_recommendations([item_eval])
    assert len(recs) > 0

    # Top recommendation should be a verified manufacturer (e.g. SAIL Bokaro or Bhilai)
    verified_recs = [r for r in recs if r.verification_status == "VERIFIED"]
    assert len(verified_recs) > 0
    top_v = verified_recs[0]
    assert top_v.source_type == "MANUFACTURER"
    assert "SAIL" in top_v.source_name
    assert top_v.score_breakdown is not None
    assert top_v.score_breakdown.compliance_evidence == 1.0
    assert any("CML-" in ev for ev in top_v.verification_evidence)

# 2. Sourcing Region Test
def test_sourcing_region_matching():
    sourcing_svc = SourcingService()
    norm = NormalizedRequirementItem(
        item_name="1.1 kV XLPE insulated electrical cables",
        category="Cable",
        quantity=2000.0,
        unit="meters",
        specifications="Working voltage 1100 V, PVC sheathed",
        mandatory_certifications=["ISI Mark"],
        inferred_standard_requirements=["IS-7098-1"],
        search_terms=["cable", "xlpe", "1.1 kv"]
    )
    matching_std = RecommendationResultItem(
        standard_id="IS-7098-1",
        is_code="IS 7098 (Part 1)",
        title="Crosslinked Polyethylene Insulated Thermoplastic Sheathed Cables",
        department="Electro-technical",
        scope_summary="Covers requirements for XLPE cables up to 1100 V.",
        key_specifications="Voltage 1.1 kV",
        testing_requirements="Conductor resistance, High voltage test",
        status="ACTIVE",
        score=0.90,
        reason="Direct match for XLPE cable."
    )
    item_eval = ItemComplianceEvaluation(
        item_id="ITEM-02",
        item_name=norm.item_name,
        normalized_profile=norm,
        standards=[matching_std],
        primary_standard=matching_std,
        compliance_status="COMPLIANT",
        score=0.90,
        applicable_scheme="ISI Mark (Scheme I)",
        is_mandatory_certification=True,
        missing_parameters=[],
        evidence=[],
        recommendation=""
    )

    recs = sourcing_svc.generate_recommendations([item_eval])
    assert len(recs) > 0
    region_recs = [r for r in recs if r.source_type == "SOURCING_REGION"]
    assert len(region_recs) > 0
    peenya = region_recs[0]
    assert peenya.verification_status == "REGION_ONLY"
    assert peenya.score_breakdown.compliance_evidence == 0.50
    assert "Peenya" in peenya.source_name

# 3. Unverified Source Test
def test_unverified_source_matching():
    sourcing_svc = SourcingService()
    source_entry = {
        "source_id": "SRC-TEST-UNVERIFIED",
        "source_name": "Sample Unregistered Trader",
        "source_type": "DISTRIBUTOR",
        "verification_status": "REQUIRES_VENDOR_VERIFICATION",
        "location": {"city": "Delhi", "state": "Delhi NCR", "latitude": 28.61, "longitude": 77.20},
        "categories": ["cable"],
        "supported_standards": ["IS-694"],
        "verification_evidence": ["Unregistered trader; vendor verification required"]
    }
    score = sourcing_svc.calculate_score(
        source=source_entry,
        item_category="cable",
        item_specs="pvc cable",
        matching_standard_ids=["IS-694"]
    )
    assert score.compliance_evidence == 0.35
    assert score.data_confidence == 0.50
    assert score.overall_score < 80.0

# 4. Standard Mismatch Test
def test_standard_mismatch():
    sourcing_svc = SourcingService()
    sail_bokaro = sourcing_svc.get_source_by_id("SRC-MFR-SAIL-BOKARO")
    assert sail_bokaro is not None
    score = sourcing_svc.calculate_score(
        source=sail_bokaro,
        item_category="cement",
        item_specs="portland pozzolana cement",
        matching_standard_ids=["IS-1489-1"]
    )
    assert score.standard_match == 0.0
    assert score.category_match == 0.0
    assert score.overall_score < 40.0

# 5. Category Mismatch Test
def test_category_mismatch():
    sourcing_svc = SourcingService()
    peenya = sourcing_svc.get_source_by_id("SRC-REG-BLR-PEENYA")
    assert peenya is not None
    score = sourcing_svc.calculate_score(
        source=peenya,
        item_category="textile",
        item_specs="cotton fabric cloth",
        matching_standard_ids=["IS-12345"]
    )
    assert score.category_match == 0.0

# 6. Missing BIS Evidence Test
def test_missing_bis_evidence():
    sourcing_svc = SourcingService()
    verified_src = sourcing_svc.get_source_by_id("SRC-MFR-SAIL-BOKARO")
    unverified_src = {
        "source_id": "SRC-UNVERIFIED-STEEL",
        "source_name": "Generic Scrap Re-roller",
        "source_type": "MANUFACTURER",
        "verification_status": "UNVERIFIED",
        "location": {"city": "Bokaro", "state": "Jharkhand", "latitude": 23.66, "longitude": 86.15},
        "categories": ["steel"],
        "supported_standards": ["IS-1786"],
        "verification_evidence": []
    }
    v_score = sourcing_svc.calculate_score(verified_src, "steel", "tmt bar", ["IS-1786"])
    u_score = sourcing_svc.calculate_score(unverified_src, "steel", "tmt bar", ["IS-1786"])

    assert v_score.compliance_evidence == 1.0
    assert u_score.compliance_evidence == 0.10
    assert v_score.overall_score > u_score.overall_score + 20.0

# 7. Multiple Possible Suppliers Ranking
def test_multiple_possible_suppliers_ranking():
    sourcing_svc = SourcingService()
    norm = NormalizedRequirementItem(
        item_name="TMT Steel Rebars",
        category="Steel",
        quantity=100.0,
        unit="tonnes",
        specifications="Fe 500D rebar per IS 1786",
        mandatory_certifications=["ISI Mark"],
        inferred_standard_requirements=["IS-1786"],
        search_terms=["steel", "rebar"]
    )
    std = RecommendationResultItem(
        standard_id="IS-1786",
        is_code="IS 1786",
        title="High Strength Deformed Steel Bars",
        department="Civil",
        scope_summary="Structural rebar",
        key_specifications="Fe 500D",
        testing_requirements="Tensile",
        status="ACTIVE",
        score=0.95,
        reason="Match"
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
        evidence=[],
        recommendation=""
    )
    recs = sourcing_svc.generate_recommendations([item_eval])
    assert len(recs) >= 2
    # Ensure descending sort
    scores = [r.suitability_score for r in recs]
    assert scores == sorted(scores, reverse=True)

# 8. Geographic Ranking Test
def test_geographic_ranking():
    sourcing_svc = SourcingService()
    sail_bokaro = sourcing_svc.get_source_by_id("SRC-MFR-SAIL-BOKARO")
    jharkhand_score = sourcing_svc.calculate_score(
        sail_bokaro, "steel", "rebar", ["IS-1786"], preferred_state="Jharkhand"
    )
    punjab_score = sourcing_svc.calculate_score(
        sail_bokaro, "steel", "rebar", ["IS-1786"], preferred_state="Punjab"
    )
    assert jharkhand_score.location_relevance == 1.0
    assert punjab_score.location_relevance < 1.0
    assert jharkhand_score.overall_score >= punjab_score.overall_score

# 9. Package with One Unsupported Item
def test_package_with_one_unsupported_item():
    pkg_svc = PackageEvaluationService()
    norm_supported = NormalizedRequirementItem(
        item_name="1.1 kV XLPE Power Cable",
        category="Cable",
        quantity=100.0,
        unit="meters",
        specifications="Working voltage 1100 V, PVC outer sheath",
        search_terms=["cable"]
    )
    std_supported = RecommendationResultItem(
        standard_id="IS-7098-1",
        is_code="IS 7098 (Part 1)",
        title="XLPE Cables",
        department="Electro-technical",
        scope_summary="XLPE Cables",
        key_specifications="1.1 kV",
        testing_requirements="High voltage test",
        status="ACTIVE",
        score=0.90,
        reason="Match"
    )
    eval_supported = ItemComplianceEvaluation(
        item_id="ITEM-01",
        item_name=norm_supported.item_name,
        normalized_profile=norm_supported,
        standards=[std_supported],
        primary_standard=std_supported,
        compliance_status="COMPLIANT",
        score=0.90,
        applicable_scheme="ISI Mark (Scheme I)",
        is_mandatory_certification=True,
        missing_parameters=[],
        evidence=["IS 7098-1"],
        recommendation=""
    )

    norm_unsupported = NormalizedRequirementItem(
        item_name="Experimental Quantum Computing Cryogenic Dilution Refrigerator",
        category="Cryogenics",
        quantity=1.0,
        unit="units",
        specifications="MilliKelvin temperature refrigeration unit",
        search_terms=["quantum", "cryogenics"]
    )
    eval_unsupported = ItemComplianceEvaluation(
        item_id="ITEM-02",
        item_name=norm_unsupported.item_name,
        normalized_profile=norm_unsupported,
        standards=[],
        primary_standard=None,
        compliance_status="ACTION_REQUIRED",
        score=0.15,
        applicable_scheme="Voluntary BIS Standard Conformity",
        is_mandatory_certification=False,
        missing_parameters=["Standard Indian nomenclature not recognized"],
        evidence=[],
        recommendation="No matching standard."
    )

    pkg_eval = pkg_svc.evaluate_package([eval_supported, eval_unsupported], sourcing_recs=[])
    assert pkg_eval.standards_coverage == 0.50
    assert pkg_eval.decision_summary is not None
    assert pkg_eval.decision_summary.all_standards_covered is False
    assert pkg_eval.decision_summary.procurement_ready is False
    assert any("ITEM-02" in u or "Cryogenic" in u for u in pkg_eval.unresolved_issues)

# 10. Package with No Sourcing Evidence
def test_package_with_no_sourcing_evidence():
    pkg_svc = PackageEvaluationService()
    norm = NormalizedRequirementItem(
        item_name="Standard Structural Component",
        category="Mechanical",
        quantity=10.0,
        specifications="Custom fabrication",
        search_terms=["custom"]
    )
    std = RecommendationResultItem(
        standard_id="IS-800",
        is_code="IS 800",
        title="Code of practice for general construction in steel",
        department="Civil",
        scope_summary="Structural steel design",
        key_specifications="Steel design",
        testing_requirements="Design verification",
        status="ACTIVE",
        score=0.75,
        reason="Match"
    )
    item_eval = ItemComplianceEvaluation(
        item_id="ITEM-01",
        item_name=norm.item_name,
        normalized_profile=norm,
        standards=[std],
        primary_standard=std,
        compliance_status="COMPLIANT",
        score=0.75,
        applicable_scheme="Voluntary",
        is_mandatory_certification=False,
        missing_parameters=[],
        evidence=[],
        recommendation=""
    )
    # Empty sourcing recommendations passed
    pkg_eval = pkg_svc.evaluate_package([item_eval], sourcing_recs=[])
    assert pkg_eval.sourcing_coverage == 0.0
    assert pkg_eval.verification_coverage == 0.0
    assert len(pkg_eval.decision_summary.insufficient_evidence_items) == 1

# 11. Gemini Unavailable Fallback
def test_gemini_unavailable_fallback():
    # Instantiate service (may or may not have a Gemini key; fallback path is what we test)
    exp_svc = ExplanationService(gemini_api_key=None)
    # Verify deterministic explanation is always returned regardless of Gemini status

    norm = NormalizedRequirementItem(item_name="Cables", category="Cable", specifications="1100 V")
    std = RecommendationResultItem(
        standard_id="IS-694",
        is_code="IS 694",
        title="PVC Cables",
        department="Electro-technical",
        scope_summary="PVC cables",
        key_specifications="1100 V",
        testing_requirements="High voltage test",
        status="ACTIVE",
        score=0.85,
        reason="Match"
    )
    item_eval = ItemComplianceEvaluation(
        item_id="ITEM-01",
        item_name="Cables",
        normalized_profile=norm,
        standards=[std],
        primary_standard=std,
        compliance_status="COMPLIANT",
        score=0.85,
        applicable_scheme="ISI Mark",
        is_mandatory_certification=True,
        missing_parameters=[],
        evidence=["IS 694"],
        recommendation=""
    )
    pkg_svc = PackageEvaluationService()
    pkg_eval = pkg_svc.evaluate_package([item_eval], sourcing_recs=[])

    explanation = exp_svc.generate_procurement_explanation(
        company="GreenTech Labs",
        items=[item_eval],
        package_eval=pkg_eval,
        sourcing_recs=[]
    )
    assert explanation is not None
    assert "GreenTech Labs" in explanation.summary
    assert len(explanation.supported_by_data) > 0
    assert any("[SUPPORTED BY DATABASE]" in s for s in explanation.supported_by_data)

# 12. Malformed Supplier Data Graceful Handling
def test_malformed_supplier_data():
    sourcing_svc = SourcingService()
    malformed_source = {
        "source_id": "MALFORMED-01",
        # missing source_name, location is broken, categories is None
        "location": {"city": "Unknown", "state": "Unknown", "latitude": "invalid", "longitude": 0.0},
        "categories": None,
        "supported_standards": None
    }
    # calculate_score should not crash
    score = sourcing_svc.calculate_score(
        source=malformed_source,
        item_category="cable",
        item_specs="wire",
        matching_standard_ids=[]
    )
    assert score.overall_score >= 0.0

# 13. Sourcing Registry API Endpoints
def test_sourcing_registry_api_endpoints():
    # GET /api/v1/procurement/sources
    res_all = client.get("/api/v1/procurement/sources")
    assert res_all.status_code == 200
    sources = res_all.json()
    assert len(sources) >= 10

    # Filter by category
    res_cable = client.get("/api/v1/procurement/sources?category=cable")
    assert res_cable.status_code == 200
    for s in res_cable.json():
        assert any("cable" in c.lower() for c in s.get("categories", []))

    # Filter by verification_status
    res_verified = client.get("/api/v1/procurement/sources?verification_status=VERIFIED")
    assert res_verified.status_code == 200
    for s in res_verified.json():
        assert s["verification_status"] == "VERIFIED"

    # GET /api/v1/procurement/sources/{source_id}
    res_single = client.get("/api/v1/procurement/sources/SRC-MFR-SAIL-BOKARO")
    assert res_single.status_code == 200
    assert res_single.json()["source_name"].startswith("Steel Authority of India")

    # 404 on nonexistent source
    res_404 = client.get("/api/v1/procurement/sources/NON_EXISTENT_ID")
    assert res_404.status_code == 404
