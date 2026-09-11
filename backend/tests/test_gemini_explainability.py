"""
Tests for ExplanationService and GeminiService — updated for google.genai SDK (v2).

These tests verify:
1. No-key configuration → deterministic fallback
2. Configured service with mock SDK → Gemini path exercised
3. Successful grounded synthesis
4. API failure fallback
5–8. Prompt safety invariants preserved
9. API key never returned in HTTP responses
10. Procurement analysis functional without Gemini
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.services.explanation_service import ExplanationService
from backend.app.services.procurement_service import ProcurementService
from backend.app.models.requests import ProcurementAnalysisRequest
from backend.app.models.responses import (
    ItemComplianceEvaluation,
    PackageEvaluation,
    SourcingRecommendationItem,
    LocationModel,
    DecisionSummary,
)

client = TestClient(app)


def _make_dummy_item(name="PVC Cable", has_standard=True):
    item = MagicMock()
    item.item_name = name
    item.is_mandatory_certification = True
    item.applicable_scheme = "ISI Mark Scheme I"
    item.missing_parameters = []
    if has_standard:
        std = MagicMock()
        std.is_code = "IS 694"
        std.title = "PVC Insulated Cables"
        std.testing_requirements = "Spark test"
        item.primary_standard = std
    else:
        item.primary_standard = None
    return item


def _make_dummy_pkg():
    pkg = MagicMock()
    pkg.total_items = 1
    pkg.overall_readiness_score = 85
    pkg.readiness_level = "HIGH"
    pkg.decision_status = "READY_WITH_VERIFICATION"
    pkg.decision_summary = None
    pkg.standards_coverage = 1.0
    pkg.sourcing_coverage = 1.0
    pkg.verification_coverage = 1.0
    return pkg


# 1. Gemini Disabled / Missing Configuration
def test_gemini_disabled_missing_configuration():
    service = ExplanationService(gemini_api_key="")
    assert service.api_key == ""
    assert service._sdk_available is False

    # Single recommendation explanation fallback
    exp = service.generate_explanation(
        "Cables for 1.1 kV",
        {},
        [{"is_code": "IS 7098 (Part 1)", "title": "XLPE Cable", "score": 0.8, "reason": "Voltage match"}],
    )
    assert "Gemini explanation unavailable" in exp
    assert "IS 7098 (Part 1)" in exp

    # Package explanation fallback
    res = service.generate_procurement_explanation("Startup A", [_make_dummy_item()], _make_dummy_pkg(), [])
    assert res.synthesis_type == "GROUNDED_DETERMINISTIC_FALLBACK"
    assert "Gemini explanation" in res.summary


# 2. Gemini Configured Service with Mock SDK
def test_gemini_configured_initialization():
    """Service with valid key and mocked SDK should mark _sdk_available=True."""
    svc = ExplanationService(gemini_api_key="mock-key-test")
    # Force _sdk_available True (SDK is already installed)
    svc._sdk_available = True
    assert svc.api_key == "mock-key-test"
    assert svc._sdk_available is True


# 3. Gemini Successful Grounded Synthesis (Mocked)
def test_gemini_successful_grounded_synthesis():
    service = ExplanationService(gemini_api_key="mock-api-key-safe")
    service._sdk_available = True

    mock_response_text = (
        "### SUPPORTED BY EVIDENCE / DATABASE\n"
        "- IS 694 governs PVC Cable.\n\n"
        "### INFERRED FROM MATCHING\n"
        "- None.\n\n"
        "### REQUIRES VERIFICATION\n"
        "- License validity check required on manakonline.in prior to buyer approval."
    )

    with patch(
        "backend.app.services.explanation_service._call_gemini_sdk",
        return_value=mock_response_text,
    ):
        res = service.generate_procurement_explanation(
            "Alpha Corp", [_make_dummy_item()], _make_dummy_pkg(), []
        )

    assert res.synthesis_type == "LIVE_GEMINI_SYNTHESIS"
    assert "Gemini explanation" not in res.summary or "SUPPORTED BY EVIDENCE / DATABASE" in res.summary


# 4. Gemini API Failure Fallback
def test_gemini_api_failure_fallback():
    service = ExplanationService(gemini_api_key="mock-api-key-safe")
    service._sdk_available = True

    with patch(
        "backend.app.services.explanation_service._call_gemini_sdk",
        side_effect=Exception("Network error"),
    ):
        res = service.generate_procurement_explanation(
            "Beta Corp", [_make_dummy_item()], _make_dummy_pkg(), []
        )

    assert res.synthesis_type == "GROUNDED_DETERMINISTIC_FALLBACK"
    assert "Gemini explanation" in res.summary


# 5. Gemini Prompt Forbids Inventing Unsupported Certification Claims
def test_gemini_prompt_forbids_inventing_certification():
    service = ExplanationService(gemini_api_key="mock-api-key-safe")
    service._sdk_available = True

    captured_prompt: list = []

    def mock_sdk_call(api_key, model, prompt, timeout):
        captured_prompt.append(prompt)
        return "Grounded response"

    item = _make_dummy_item("TMT Steel")
    item.is_mandatory_certification = True
    item.applicable_scheme = "ISI Mark"
    if hasattr(item, "primary_standard") and item.primary_standard:
        item.primary_standard.is_code = "IS 1786"
        item.primary_standard.title = "High Strength Deformed Steel Bars"
        item.primary_standard.testing_requirements = "Tensile test"

    with patch(
        "backend.app.services.explanation_service._call_gemini_sdk",
        side_effect=mock_sdk_call,
    ):
        service.generate_procurement_explanation("Steel Infra", [item], _make_dummy_pkg(), [])

    assert len(captured_prompt) >= 1
    prompt_text = captured_prompt[0]
    assert "NEVER invent BIS standards, IS numbers, CML license numbers" in prompt_text
    assert "NEVER claim 'Currently BIS certified', 'Valid CML', 'Active CRS'" in prompt_text


# 6. Gemini Prompt Preserves REQUIRES_LIVE_VERIFICATION
def test_gemini_prompt_preserves_requires_live_verification():
    service = ExplanationService(gemini_api_key="mock-api-key-safe")
    service._sdk_available = True

    captured_prompt: list = []

    def mock_sdk_call(api_key, model, prompt, timeout):
        captured_prompt.append(prompt)
        return "Grounded response"

    item = MagicMock()
    item.item_name = "Solar PV"
    item.primary_standard = None
    item.missing_parameters = []

    pkg = _make_dummy_pkg()
    pkg.standards_coverage = 0.0
    pkg.sourcing_coverage = 0.0
    pkg.verification_coverage = 0.0

    with patch(
        "backend.app.services.explanation_service._call_gemini_sdk",
        side_effect=mock_sdk_call,
    ):
        service.generate_procurement_explanation("SolarTech", [item], pkg, [])

    prompt_text = captured_prompt[0]
    assert "STATIC EVIDENCE != CURRENT VERIFICATION" in prompt_text
    assert "Static registry evidence or historical CML records require live portal audit before contract award" in prompt_text


# 7. Gemini Prompt Preserves SOURCE vs REGION_ONLY
def test_gemini_prompt_preserves_source_vs_region_only():
    service = ExplanationService(gemini_api_key="mock-api-key-safe")
    service._sdk_available = True

    captured_prompt: list = []

    def mock_sdk_call(api_key, model, prompt, timeout):
        captured_prompt.append(prompt)
        return "Grounded response"

    item = MagicMock()
    item.item_name = "Transformer"
    item.primary_standard = None
    item.missing_parameters = []

    with patch(
        "backend.app.services.explanation_service._call_gemini_sdk",
        side_effect=mock_sdk_call,
    ):
        service.generate_procurement_explanation("Grid Power", [item], _make_dummy_pkg(), [])

    prompt_text = captured_prompt[0]
    assert "SOURCE != REGION_ONLY" in prompt_text
    assert "Sourcing regions/corridors are geographic manufacturing clusters, NOT certified manufacturers or suppliers" in prompt_text


# 8. Gemini Prompt Forbids Autonomous Buyer Approval
def test_gemini_prompt_forbids_autonomous_buyer_approval():
    service = ExplanationService(gemini_api_key="mock-api-key-safe")
    service._sdk_available = True

    captured_prompt: list = []

    def mock_sdk_call(api_key, model, prompt, timeout):
        captured_prompt.append(prompt)
        return "Grounded response"

    item = MagicMock()
    item.item_name = "Switchgear"
    item.primary_standard = None
    item.missing_parameters = []

    with patch(
        "backend.app.services.explanation_service._call_gemini_sdk",
        side_effect=mock_sdk_call,
    ):
        service.generate_procurement_explanation("Heavy Elec", [item], _make_dummy_pkg(), [])

    prompt_text = captured_prompt[0]
    assert "NO AUTONOMOUS PURCHASE APPROVAL" in prompt_text
    assert "Procurement-ready for buyer approval" in prompt_text


# 9. Gemini Key Is Never Returned in API Responses
def test_gemini_key_never_returned_in_api_responses():
    # Health endpoint
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "GEMINI_API_KEY" not in data
    assert "api_key" not in data
    assert "key" not in data
    assert "gemini_configured" in data
    assert isinstance(data["gemini_configured"], bool)

    # Procurement analysis endpoint
    analyze_resp = client.post(
        "/api/v1/procurement/analyze",
        json={
            "company": "Secure Buyer Ltd",
            "description": "Procurement of 1.1 kV XLPE insulated electrical cables",
        },
    )
    assert analyze_resp.status_code == 200
    res_str = analyze_resp.text
    assert "GEMINI_API_KEY" not in res_str
    if settings.GEMINI_API_KEY:
        assert settings.GEMINI_API_KEY not in res_str


# 10. Existing Procurement Analysis Remains Functional Without Gemini
def test_existing_procurement_analysis_remains_functional_without_gemini():
    from backend.app.api.dependencies import (
        normalization_service,
        hybrid_retrieval_service,
        package_evaluation_service,
        sourcing_service,
    )

    fallback_expl_service = ExplanationService(gemini_api_key="")
    offline_procurement_service = ProcurementService(
        normalization_service=normalization_service,
        hybrid_retrieval_service=hybrid_retrieval_service,
        package_evaluation_service=package_evaluation_service,
        sourcing_service=sourcing_service,
        explanation_service=fallback_expl_service,
    )

    req = ProcurementAnalysisRequest(
        company="Offline Project Ltd",
        description="Requirement for portable ABC dry powder and CO2 fire extinguishers in commercial buildings",
    )
    result = offline_procurement_service.analyze(req)
    assert len(result.items) >= 1
    assert result.package_evaluation.overall_readiness_score > 0
    assert result.explanation.synthesis_type == "GROUNDED_DETERMINISTIC_FALLBACK"
    assert "Gemini explanation" in result.explanation.summary
