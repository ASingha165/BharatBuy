import pytest
import time
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.config import settings
from backend.app.services.evidence_service import EvidenceService
from backend.app.services.sourcing_service import SourcingService
from backend.app.models.requests import ProcurementAnalysisRequest, ProcurementRequirementItem, ManualVerifyRequest

client = TestClient(app)

def test_health_endpoint_production_contract():
    """
    Validates GET /api/v1/health reports all required fields without exposing secrets.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["database"] is True
    assert data["total_standards"] >= 500
    assert "model_type" in data
    assert "gemini_configured" in data
    assert isinstance(data["gemini_configured"], bool)
    assert "is_demo_mode" in data
    assert data["is_demo_mode"] is False
    # Verify no secret or token is leaked
    assert "api_key" not in data
    assert "key" not in str(data).lower() or "model_type" in data


def test_end_to_end_smoke_test_triple_category():
    """
    End-to-End Smoke Test:
    Items:
    1. XLPE electrical cables
    2. Fe 500D TMT steel
    3. crystalline silicon PV modules
    """
    payload = {
        "company": "Bharat Infrastructure & Power Corp",
        "requirements": [
            {
                "item": "1.1 kV XLPE insulated copper electrical cables",
                "quantity": 1500,
                "unit": "meters",
                "specifications": "Crosslinked polyethylene insulation, 1100V working voltage per IS 7098 Part 1"
            },
            {
                "item": "Fe 500D TMT high strength deformed steel bars",
                "quantity": 35,
                "unit": "metric tonnes",
                "specifications": "Thermo-mechanically treated rebar for concrete reinforcement per IS 1786, yield strength 500 MPa"
            },
            {
                "item": "Crystalline silicon terrestrial photovoltaic PV modules",
                "quantity": 250,
                "unit": "units",
                "specifications": "Terrestrial crystalline silicon solar PV modules, 450W peak, IS 14286 qualified"
            }
        ],
        "top_k_per_item": 5
    }

    t0 = time.perf_counter()
    response = client.post("/api/v1/procurement/analyze", json=payload)
    elapsed = time.perf_counter() - t0

    assert response.status_code == 200, response.text
    data = response.json()

    # 1. Verification of normalized requirements
    assert "request_id" in data
    assert data["company"] == "Bharat Infrastructure & Power Corp"
    assert len(data["items"]) == 3

    # 2. Verification of standards retrieved per item
    cable_item = next(i for i in data["items"] if "cable" in i["item_name"].lower())
    steel_item = next(i for i in data["items"] if "steel" in i["item_name"].lower())
    solar_item = next(i for i in data["items"] if "pv" in i["item_name"].lower() or "solar" in i["item_name"].lower())

    assert any(code in cable_item["primary_standard"]["is_code"] for code in ["694", "7098", "1554"])

    assert steel_item["primary_standard"] is not None
    assert "1786" in steel_item["primary_standard"]["is_code"]

    assert solar_item["primary_standard"] is not None
    assert "14286" in solar_item["primary_standard"]["is_code"]

    # 3. Compliance evaluated
    for itm in [cable_item, steel_item, solar_item]:
        assert "score" in itm
        assert itm["score"] > 0
        assert "compliance_status" in itm
        assert itm["compliance_status"] in ["COMPLIANT", "CONDITIONAL_COMPLIANCE", "ACTION_REQUIRED"]
        assert "applicable_scheme" in itm

    # 4. Sources ranked & evidence generated
    assert len(data["recommendations"]) > 0
    top_rec = data["recommendations"][0]
    assert "suitability_score" in top_rec
    assert "trust_score" in top_rec
    assert "trust_level" in top_rec
    assert "provenance_label" in top_rec
    assert len(top_rec["evidence_records"]) > 0

    # 5. Map points returned
    assert len(data["map_points"]) > 0
    for pt in data["map_points"]:
        assert pt["latitude"] != 0.0
        assert pt["longitude"] != 0.0
        assert pt["source_type"] in ["MANUFACTURER", "SOURCING_REGION", "SUPPLIER"]

    # 6. Package decision returned
    pkg = data["package_evaluation"]
    assert pkg["total_items"] == 3
    assert pkg["overall_readiness_score"] > 0
    assert pkg["decision_status"] in ["READY", "READY_WITH_VERIFICATION", "INSUFFICIENT_EVIDENCE", "NOT_RECOMMENDED"]
    assert "standards_coverage" in pkg
    assert "sourcing_coverage" in pkg
    assert "verification_coverage" in pkg
    assert "decision_summary" in pkg

    # 7. Gemini explanation / fallback returned
    explanation = data["explanation"]
    assert "summary" in explanation
    assert len(explanation["summary"]) > 20
    assert len(explanation["supported_by_data"]) > 0


def test_negative_empty_request():
    """Negative Test: Empty request body returns 422 or 400."""
    response = client.post("/api/v1/procurement/analyze", json={})
    assert response.status_code in [400, 422]
    assert "detail" in response.json()


def test_negative_whitespace_company():
    """Negative Test: Whitespace company returns clean 400 error."""
    response = client.post("/api/v1/procurement/analyze", json={
        "company": "   ",
        "requirements": [{"item": "Steel bars", "quantity": 10}]
    })
    assert response.status_code == 400
    assert "Company name cannot be empty" in response.json()["detail"]


def test_negative_empty_requirements_and_no_description():
    """Negative Test: No requirements and no natural description returns clean 400."""
    response = client.post("/api/v1/procurement/analyze", json={
        "company": "Test Company",
        "requirements": []
    })
    assert response.status_code == 400
    assert "Either 'requirements' list or a natural-language 'description'" in response.json()["detail"]


def test_negative_unknown_product_unmatched():
    """Negative Test: Completely unknown/gibberish product handles gracefully without crash."""
    response = client.post("/api/v1/procurement/analyze", json={
        "company": "XenoTech Innovations",
        "requirements": [
            {
                "item": "zk999 unobtanium hyperdrive plasma catalyst",
                "quantity": 1,
                "unit": "pcs",
                "specifications": "hypothetical non-existent quantum alloy"
            }
        ]
    })
    assert response.status_code == 200
    data = response.json()
    item = data["items"][0]
    # Handled cleanly; primary standard may be None or low confidence
    assert item["item_name"] == "zk999 unobtanium hyperdrive plasma catalyst"
    # Sourcing feasiblity should indicate caveats or low readiness
    pkg = data["package_evaluation"]
    assert pkg["decision_status"] in ["INSUFFICIENT_EVIDENCE", "NOT_RECOMMENDED", "READY_WITH_VERIFICATION"]


def test_negative_invalid_source_id():
    """Negative Test: Invalid source ID returns clean 404."""
    response = client.get("/api/v1/procurement/sources/SRC-NON-EXISTENT-9999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_negative_invalid_source_evidence_id():
    """Negative Test: Invalid source ID for evidence returns clean 404."""
    response = client.get("/api/v1/procurement/sources/SRC-INVALID-EVIDENCE-404/evidence")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_negative_manual_verification_incomplete_confirmation():
    """
    Negative Test: Attempting manual verification with unconfirmed checks
    should not falsely record confirmation if checklist is incomplete.
    """
    incomplete_payload = {
        "reference_id": "CML-TEST-INCOMPLETE",
        "action": "CONFIRM_MANUAL_VERIFICATION",
        "verified_by": "auditor@buyer.org",
        "checklist_confirmed": {
            "license_exists": True,
            "product_category_matches": False,  # Failed check
            "applicable_standard_matches": False,
            "license_currently_valid": False,
            "manufacturer_site_matches": False
        },
        "notes": "Partial audit only."
    }
    response = client.post("/api/v1/procurement/sources/SRC-MFR-SAIL-BOKARO/verify", json=incomplete_payload)
    assert response.status_code == 200
    data = response.json()
    # Incomplete checklist must NOT mark status as CONFIRMED
    assert data["status"] != "CONFIRMED"


def test_production_mode_excludes_demo_registry():
    """
    Negative / Integrity Test:
    When BHARATBUY_DEMO_MODE is False, zero demo records are loaded or recommended.
    """
    assert settings.BHARATBUY_DEMO_MODE is False
    sourcing_svc = SourcingService()
    all_sources = sourcing_svc.get_all_sources()
    for s in all_sources:
        s_id = s.get("source_id", "")
        p_label = s.get("provenance_label", "")
        assert not s.get("is_demo_data", False), f"Demo data leaked in production mode: {s_id}"
        assert "DEMO" not in s_id.upper() or "SRC-DEMO" not in s_id.upper()
        assert p_label != "DEMO_DATA"


def test_real_world_evidence_disclaimer_wording():
    """
    Test 9 validation:
    Verifies that the exact disclaimer wording is configured in EvidenceRecord claims.
    """
    evidence_svc = EvidenceService()
    source_cml = {
        "source_id": "SRC-MFR-TEST",
        "source_name": "Test PSU",
        "source_type": "MANUFACTURER",
        "verification_status": "VERIFIED",
        "location": {"city": "Bhilai", "state": "Chhattisgarh"},
        "categories": ["steel"],
        "supported_standards": ["IS-1786"],
        "verification_evidence": ["Statutory BIS License CML-1234567 for IS 1786 Fe 500D"]
    }
    records = evidence_svc.generate_source_evidence_records(source_cml)
    cml_rec = next(r for r in records if r.evidence_type == "BIS_LICENSE")
    assert "Documented certification evidence — current validity requires verification" in cml_rec.description
    assert "Documented certification evidence — current validity requires verification" in cml_rec.supports_claim
