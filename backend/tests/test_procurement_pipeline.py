import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.requests import ProcurementRequirementItem, ProcurementAnalysisRequest
from backend.app.services.normalization_service import NormalizationService
from backend.app.services.package_evaluation_service import PackageEvaluationService
from backend.app.services.sourcing_service import SourcingService
from backend.app.api.dependencies import hybrid_retrieval_service, procurement_service

client = TestClient(app)

def test_normalization_service_item():
    norm_svc = NormalizationService()
    item = ProcurementRequirementItem(
        item="1.1 kV XLPE insulated electrical cables",
        quantity=500,
        unit="meters",
        specifications="Crosslinked polyethylene insulation, PVC sheathed, 1100 V rating, ISI marked"
    )
    res = norm_svc.normalize_item(item, index=1)
    assert res.category == "Cable"
    assert res.quantity == 500.0
    assert res.unit == "meters"
    assert any("1.1" in s or "1100" in s for s in res.inferred_standard_requirements)
    assert "ISI Mark" in res.mandatory_certifications

def test_normalization_natural_language_parsing():
    norm_svc = NormalizationService()
    nl_text = """
    - 500 meters of 1.1 kV PVC power cables
    - 200 units of crystalline silicon solar PV panels
    - 50 tonnes of Fe 500 TMT steel rebar
    """
    items = norm_svc.parse_natural_language_requirements(nl_text)
    assert len(items) >= 3
    assert any("cable" in i.item.lower() for i in items)
    assert any("solar" in i.item.lower() for i in items)
    assert any("steel" in i.item.lower() or "rebar" in i.item.lower() for i in items)

def test_hybrid_retrieval_cables():
    results = hybrid_retrieval_service.retrieve_and_rank("1.1 kV XLPE insulated underground power cables", top_k=5)
    assert len(results) > 0
    codes = [r.is_code for r in results]
    assert any("7098" in c or "1554" in c or "694" in c for c in codes)
    assert results[0].score > 0.40

def test_hybrid_retrieval_steel_concrete():
    results = hybrid_retrieval_service.retrieve_and_rank("Fe 500 high strength deformed steel bars for concrete reinforcement", top_k=5)
    assert len(results) > 0
    codes = [r.is_code for r in results]
    assert any("1786" in c or "456" in c or "2062" in c for c in codes)

def test_item_compliance_evaluation():
    norm_svc = NormalizationService()
    pkg_svc = PackageEvaluationService()

    req = ProcurementRequirementItem(
        item="Underground power distribution cables",
        quantity=1000,
        unit="meters",
        specifications="Low voltage power cable"
    )
    normalized = norm_svc.normalize_item(req)
    stds = hybrid_retrieval_service.retrieve_and_rank(f"{req.item} {req.specifications}", top_k=3)
    item_eval = pkg_svc.evaluate_item_compliance("ITEM-01", normalized, stds)

    assert item_eval.item_id == "ITEM-01"
    assert item_eval.applicable_scheme == "ISI Mark (Scheme I)"
    assert item_eval.is_mandatory_certification is True
    # Missing voltage was detected
    assert any("voltage" in p.lower() for p in item_eval.missing_parameters)

def test_package_evaluation_metrics():
    norm_svc = NormalizationService()
    pkg_svc = PackageEvaluationService()

    items_data = [
        ("1.1 kV XLPE power cables", "1100 V working voltage, PVC sheath"),
        ("Fe 500 TMT structural steel rebar", "High yield strength deformed bars per IS 1786"),
    ]
    eval_items = []
    for idx, (itm, specs) in enumerate(items_data, 1):
        req = ProcurementRequirementItem(item=itm, specifications=specs)
        norm = norm_svc.normalize_item(req, idx)
        stds = hybrid_retrieval_service.retrieve_and_rank(f"{itm} {specs}", top_k=3)
        eval_items.append(pkg_svc.evaluate_item_compliance(f"ITEM-{idx:02d}", norm, stds))

    pkg_eval = pkg_svc.evaluate_package(eval_items)
    assert pkg_eval.total_items == 2
    assert pkg_eval.overall_readiness_score >= 50.0
    assert pkg_eval.readiness_level in ["HIGH", "MODERATE"]
    assert pkg_eval.item_coverage > 0.0

def test_sourcing_service_hubs_and_map():
    sourcing_svc = SourcingService()
    norm_svc = NormalizationService()
    pkg_svc = PackageEvaluationService()

    req = ProcurementRequirementItem(item="1.1 kV power distribution cables", specifications="PVC cables")
    norm = norm_svc.normalize_item(req)
    stds = hybrid_retrieval_service.retrieve_and_rank(req.item, top_k=3)
    item_eval = pkg_svc.evaluate_item_compliance("ITEM-01", norm, stds)

    recs = sourcing_svc.generate_recommendations([item_eval])
    assert len(recs) > 0
    top_rec = recs[0]
    assert top_rec.latitude != 0.0
    assert top_rec.source_type in ["SOURCING_REGION", "VERIFIED_INDUSTRIAL_HUB", "MANUFACTURER", "DISTRIBUTOR"]
    assert top_rec.verification_status in ["REGION_ONLY", "VERIFIED_HUB", "VERIFIED", "REQUIRES_VENDOR_VERIFICATION"]

    map_points = sourcing_svc.build_map_points(recs)
    assert len(map_points) > 0
    assert map_points[0].latitude == top_rec.latitude

def test_procurement_api_end_to_end():
    payload = {
        "company": "Zenith Solar & Infrastructure Ltd",
        "requirements": [
            {
                "item": "1.1 kV XLPE insulated underground power distribution cables",
                "quantity": 5000,
                "unit": "meters",
                "specifications": "Working voltage 1100 V, XLPE insulation, galvanized steel armor, outer PVC sheath"
            },
            {
                "item": "Fe 500 High strength deformed TMT steel bars",
                "quantity": 30,
                "unit": "tonnes",
                "specifications": "Reinforcement steel for foundation slabs, yield strength 500 MPa"
            }
        ],
        "top_k_per_item": 3
    }
    # Test primary endpoint
    response = client.post("/api/v1/procurement/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["request_id"].startswith("PROC-")
    assert data["company"] == "Zenith Solar & Infrastructure Ltd"
    assert len(data["items"]) == 2
    assert data["package_evaluation"]["overall_readiness_score"] >= 60.0
    assert len(data["recommendations"]) > 0
    assert len(data["map_points"]) > 0
    assert "summary" in data["explanation"]
    assert len(data["explanation"]["supported_by_data"]) > 0

    # Test direct alias endpoint /api/procurement/analyze
    alias_res = client.post("/api/procurement/analyze", json=payload)
    assert alias_res.status_code == 200
    assert alias_res.json()["company"] == "Zenith Solar & Infrastructure Ltd"

def test_procurement_api_natural_language_input():
    payload = {
        "company": "AgriSolar Startup LLP",
        "description": "We need to procure 100 crystalline silicon solar PV panels and 5 grid-tied solar inverters for an agricultural water pumping project."
    }
    response = client.post("/api/v1/procurement/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1
    assert data["package_evaluation"]["total_items"] >= 1

def test_procurement_api_validation_errors():
    # Empty company (fails Pydantic min_length or route validation)
    res1 = client.post("/api/v1/procurement/analyze", json={"company": "", "requirements": []})
    assert res1.status_code in [400, 422]

    # Missing requirements and description
    res2 = client.post("/api/v1/procurement/analyze", json={"company": "Test Corp", "requirements": []})
    assert res2.status_code == 400

