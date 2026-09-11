"""
Test and validate the 10 required production scenarios for BharatBuy.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.explanation_service import ExplanationService
from backend.app.services.package_evaluation_service import PackageEvaluationService
from backend.app.models.responses import (
    PackageEvaluation,
    SourcingRecommendationItem,
    ScoreBreakdown,
    LocationModel,
    ItemComplianceEvaluation,
    NormalizedRequirementItem
)

client = TestClient(app)

def test_scenario_1_triple_category():
    """Scenario 1: Multi-category package (Cable + TMT + PV)."""
    payload = {
        "company": "Adani Green Energy Ltd",
        "requirements": [
            {"item": "1.1 kV XLPE insulated electrical cables", "quantity": 1000, "unit": "meters", "specifications": "1100V working voltage, IS 7098 Part 1"},
            {"item": "Fe 500D TMT high strength steel bars", "quantity": 25, "unit": "tonnes", "specifications": "Concrete reinforcement per IS 1786"},
            {"item": "Crystalline silicon solar PV modules", "quantity": 200, "unit": "modules", "specifications": "450W mono-crystalline per IS 14286"}
        ]
    }
    res = client.post("/api/v1/procurement/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 3
    assert len(data["recommendations"]) > 0
    assert len(data["map_points"]) > 0
    # Sourcing decision accurately reflects available production evidence
    assert data["package_evaluation"]["decision_status"] in ["READY", "READY_WITH_VERIFICATION", "INSUFFICIENT_EVIDENCE"]

def test_scenario_2_multiple_procurement_items():
    """Scenario 2: Multiple procurement items (4 items across civil & electrical)."""
    payload = {
        "company": "L&T Construction",
        "requirements": [
            {"item": "1.1 kV XLPE cable", "quantity": 500, "unit": "meters", "specifications": "IS 7098"},
            {"item": "Fe 500 TMT steel rebar", "quantity": 10, "unit": "tonnes", "specifications": "IS 1786"},
            {"item": "Portland Pozzolana Cement", "quantity": 100, "unit": "bags", "specifications": "IS 1489 Part 1"},
            {"item": "Solar PV module", "quantity": 50, "unit": "units", "specifications": "IS 14286"}
        ]
    }
    res = client.post("/api/v1/procurement/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 4
    assert data["package_evaluation"]["overall_readiness_score"] > 50

def test_scenario_3_empty_request_400():
    """Scenario 3: Empty request validation failure returns 400."""
    res1 = client.post("/api/v1/procurement/analyze", json={"company": "", "requirements": []})
    assert res1.status_code in [400, 422]
    res2 = client.post("/api/v1/procurement/analyze", json={"company": "Acme", "requirements": []})
    assert res2.status_code == 400

def test_scenario_4_unknown_item():
    """Scenario 4: Unknown / obscure item receives low match score and ACTION_REQUIRED."""
    payload = {
        "company": "SciFi Research Labs",
        "requirements": [
            {"item": "Graviton warp pulse synchronizer unit", "quantity": 1, "unit": "unit", "specifications": "Tachyon containment"}
        ]
    }
    res = client.post("/api/v1/procurement/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["score"] < 0.60
    assert data["items"][0]["compliance_status"] == "ACTION_REQUIRED"

def test_scenario_5_no_standard_low_match():
    """Scenario 5: Non-standard items yield 0.0 item_coverage for high-confidence standards."""
    payload = {
        "company": "Exotic Materials LLC",
        "requirements": [
            {"item": "Unobtanium crystal lattice matrix", "quantity": 2, "unit": "kg", "specifications": "Superconducting at 500K"}
        ]
    }
    res = client.post("/api/v1/procurement/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    # item_coverage is 0.0 since no standard scores above high-confidence threshold
    assert data["package_evaluation"]["item_coverage"] == 0.0

def test_scenario_6_no_sourcing():
    """Scenario 6: Zero sourcing evaluates to 0.0 sourcing coverage."""
    pkg_svc = PackageEvaluationService()
    norm = NormalizedRequirementItem(item_name="Deep Sea Submersible", category="Marine")
    item = ItemComplianceEvaluation(
        item_id="ITEM-01",
        item_name="Deep Sea Submersible",
        normalized_profile=norm,
        score=0.2,
        compliance_status="ACTION_REQUIRED",
        applicable_scheme="None",
        is_mandatory_certification=False,
        missing_parameters=["Depth rating"],
        testing_requirements=[]
    )
    pkg = pkg_svc.evaluate_package(
        [item],
        []
    )
    assert pkg.sourcing_coverage == 0.0
    assert pkg.decision_status in ["INSUFFICIENT_EVIDENCE", "NOT_RECOMMENDED"]

def test_scenario_7_insufficient_evidence():
    """Scenario 7: Sourcing with unmapped items leads to INSUFFICIENT_EVIDENCE."""
    pkg_svc = PackageEvaluationService()
    norm = NormalizedRequirementItem(item_name="Titanium Alloy Valve", category="Mechanical")
    item = ItemComplianceEvaluation(
        item_id="ITEM-01",
        item_name="Titanium Alloy Valve",
        normalized_profile=norm,
        score=0.85,
        compliance_status="COMPLIANT",
        applicable_scheme="ISI Mark",
        is_mandatory_certification=True,
        missing_parameters=[],
        testing_requirements=[]
    )
    rec = SourcingRecommendationItem(
        source_id="SRC-NONE",
        source_name="Unknown Distributor",
        source_type="SUPPLIER",
        verification_status="UNVERIFIED",
        bis_certification_status="NO_EVIDENCE",
        location=LocationModel(state="Unknown", city="Unknown", latitude=20.0, longitude=78.0),
        suitability_score=0.3,
        confidence=0.2,
        trust_score=0.1,
        trust_level="LOW",
        provenance_label="SUPPLIER_DECLARATION",
        score_breakdown=ScoreBreakdown(category_match=0.1, standard_match=0.1, compliance_evidence=0.1, location_relevance=0.1, data_confidence=0.1, overall_score=10.0),
        supported_items=["Other Product"],
        evidence_records=[]
    )
    pkg = pkg_svc.evaluate_package(
        [item],
        [rec]
    )
    assert pkg.decision_status in ["INSUFFICIENT_EVIDENCE", "NOT_RECOMMENDED"]

def test_scenario_8_requires_verification():
    """Scenario 8: Package with unverified CML license evaluates to READY_WITH_VERIFICATION."""
    payload = {
        "company": "Smart City Infra",
        "requirements": [
            {"item": "1.1 kV XLPE insulated electrical cables", "quantity": 1000, "unit": "meters", "specifications": "IS 7098 Part 1"}
        ]
    }
    res = client.post("/api/v1/procurement/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["package_evaluation"]["decision_status"] == "READY_WITH_VERIFICATION"
    summary = data["package_evaluation"]["decision_summary"]
    assert summary is not None
    assert "READY WITH VERIFICATION" in summary["summary_text"]
    assert len(summary["missing_verifications"]) > 0

def test_scenario_9_gemini_unavailable_fallback():
    """Scenario 9: Deterministic fallback message when Gemini AI is unconfigured or unavailable."""
    expl_svc = ExplanationService()
    expl_svc.client = None  # Simulate Gemini unavailable
    pkg_eval = PackageEvaluation(
        total_items=1,
        overall_readiness_score=85.0,
        readiness_level="HIGH",
        decision_status="READY_WITH_VERIFICATION",
        item_coverage=1.0,
        standards_coverage=1.0,
        compliance_coverage=1.0,
        sourcing_coverage=1.0,
        evidence_coverage=0.8,
        verification_coverage=0.0,
        sourcing_feasibility="FEASIBLE"
    )
    explanation = expl_svc.generate_procurement_explanation("Test Co", [], pkg_eval, [])
    assert "Gemini explanation" in explanation.summary
    assert "unavailable" in explanation.summary
    assert "retrieved standards and registered source evidence" in explanation.summary

def test_scenario_10_backend_health_and_error_handling():
    """Scenario 10: Health check integrity, CORS, and clean error handling without secret leaks."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "database" in data
    assert "model_type" in data
    # Ensure no API keys or secret tokens are leaked in health payload
    assert "api_key" not in data
    assert "gemini_api_key" not in data
    
    # Verify 404 for non-existent endpoint
    res_404 = client.get("/api/v1/unknown_route")
    assert res_404.status_code == 404
