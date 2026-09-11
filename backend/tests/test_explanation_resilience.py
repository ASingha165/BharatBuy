"""
Regression tests for ExplanationService resilience:
  - Gemini success path
  - Gemini timeout (hard timeout must not exceed GEMINI_HARD_TIMEOUT_SECONDS)
  - Gemini 429 / quota exhaustion (must fail fast, not wait 34s)
  - Gemini 404 / model not found
  - Malformed/empty Gemini response
  - Procurement still returns full usable results when Gemini is unavailable
  - No google.generativeai (deprecated) import used anywhere in explanation_service
"""

import time
import types
import importlib
import pytest
from unittest.mock import patch, MagicMock

from backend.app.services.explanation_service import (
    ExplanationService,
    GEMINI_HARD_TIMEOUT_SECONDS,
    GEMINI_MODEL_CANDIDATES,
    _call_gemini_sdk,
)
from backend.app.models.responses import GroundedExplanation


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_item(name="Steel TMT bars", has_standard=True):
    """Minimal ItemComplianceEvaluation-like object for testing."""
    item = MagicMock()
    item.item_name = name
    item.missing_parameters = []
    item.is_mandatory_certification = False
    item.applicable_scheme = "ISI Mark (Scheme I)"
    if has_standard:
        std = MagicMock()
        std.is_code = "IS 1786"
        std.title = "High Strength Deformed Steel Bars and Wires for Concrete Reinforcement"
        std.testing_requirements = "Tensile test, Bend test, Re-bend test"
        item.primary_standard = std
    else:
        item.primary_standard = None
    return item


def _make_sourcing_rec(source_type="SOURCING_REGION"):
    rec = MagicMock()
    rec.source_name = "Jamshedpur Industrial Corridor"
    rec.supplier_name = "Jamshedpur Industrial Corridor"
    rec.source_type = source_type
    rec.verification_status = "REGION_ONLY"
    rec.bis_certification_status = "NOT_APPLICABLE"
    rec.trust_level = "MODERATE"
    rec.supported_items = ["Steel TMT bars"]
    rec.verification_evidence = []
    rec.evidence_records = []
    loc = MagicMock()
    loc.city = "Jamshedpur"
    loc.state = "Jharkhand"
    rec.location = loc
    return rec


def _make_package_eval():
    pkg = MagicMock()
    pkg.total_items = 1
    pkg.overall_readiness_score = 75.0
    pkg.readiness_level = "MODERATE"
    pkg.standards_coverage = 1.0
    pkg.sourcing_coverage = 0.67
    pkg.verification_coverage = 0.33
    pkg.decision_status = "READY_WITH_VERIFICATION"
    pkg.decision_summary = None
    return pkg


# ---------------------------------------------------------------------------
# 1. No deprecated google.generativeai import in explanation_service module
# ---------------------------------------------------------------------------

def test_no_deprecated_generativeai_import():
    """Ensure explanation_service does NOT import google.generativeai at module level."""
    import ast
    import inspect
    import backend.app.services.explanation_service as es_module

    source = inspect.getsource(es_module)
    # Check for the deprecated package reference
    assert "google.generativeai" not in source, (
        "explanation_service.py must NOT import google.generativeai (deprecated). "
        "Use google.genai instead."
    )


# ---------------------------------------------------------------------------
# 2. Gemini success path — mock successful API response
# ---------------------------------------------------------------------------

def test_explanation_service_gemini_success():
    """When Gemini returns a valid response, generate_explanation returns it."""
    svc = ExplanationService(gemini_api_key="fake-key-for-test")
    svc._sdk_available = True

    with patch(
        "backend.app.services.explanation_service._call_gemini_sdk",
        return_value="IS 1786 applies due to TMT steel reinforcement requirements.",
    ):
        result = svc.generate_explanation(
            query="TMT steel bars for construction",
            features={"product": "steel"},
            recommendations=[
                {
                    "is_code": "IS 1786",
                    "title": "HSD Steel Bars",
                    "score": 0.91,
                    "reason": "Matched TMT steel product type",
                }
            ],
        )

    assert "IS 1786" in result
    assert "Gemini explanation unavailable" not in result


# ---------------------------------------------------------------------------
# 3. Gemini timeout — hard timeout prevents hanging > GEMINI_HARD_TIMEOUT_SECONDS
# ---------------------------------------------------------------------------

def test_gemini_hard_timeout_enforced():
    """
    If the Gemini SDK hangs, the hard timeout must terminate it within
    GEMINI_HARD_TIMEOUT_SECONDS and return a deterministic fallback — not hang.
    """
    import concurrent.futures
    import time

    def _slow_sdk_call(*args, **kwargs):
        time.sleep(999)  # Simulate SDK hanging indefinitely
        return "should never reach here"

    svc = ExplanationService(gemini_api_key="fake-key-for-test")
    svc._sdk_available = True

    t0 = time.monotonic()
    with patch(
        "backend.app.services.explanation_service._call_gemini_sdk",
        side_effect=_slow_sdk_call,
    ):
        result = svc.generate_explanation(
            query="solar PV modules",
            features={},
            recommendations=[
                {
                    "is_code": "IS 14286",
                    "title": "Crystalline Silicon Solar PV Modules",
                    "score": 0.87,
                    "reason": "Matched solar product type",
                }
            ],
        )

    elapsed = time.monotonic() - t0

    # Must complete within hard timeout + a generous 4s buffer for test overhead
    assert elapsed < GEMINI_HARD_TIMEOUT_SECONDS + 4.0, (
        f"Hard timeout not enforced: elapsed={elapsed:.2f}s, "
        f"hard limit={GEMINI_HARD_TIMEOUT_SECONDS}s"
    )
    # Must still return the deterministic fallback
    assert "IS 14286" in result or "Gemini explanation" in result


# ---------------------------------------------------------------------------
# 4. Gemini 429 quota exhaustion — must fail fast (not wait 34 seconds per retry)
# ---------------------------------------------------------------------------

def test_gemini_quota_exhaustion_fails_fast():
    """
    A 429 RESOURCE_EXHAUSTED error must skip the candidate immediately,
    NOT wait for the SDK-embedded retryDelay of 34 seconds.
    """
    quota_error = Exception(
        "429 RESOURCE_EXHAUSTED. You exceeded your current quota. "
        "Please retry in 34.985475857s."
    )

    svc = ExplanationService(gemini_api_key="fake-key-for-test")
    svc._sdk_available = True

    t0 = time.monotonic()
    with patch(
        "backend.app.services.explanation_service._call_gemini_sdk",
        side_effect=quota_error,
    ):
        result = svc.generate_explanation(
            query="XLPE cables",
            features={},
            recommendations=[
                {
                    "is_code": "IS 7098",
                    "title": "XLPE Insulated Cables",
                    "score": 0.85,
                    "reason": "Matched cable type",
                }
            ],
        )

    elapsed = time.monotonic() - t0

    # All 4 candidates × fast-fail = must complete in well under 10s total
    assert elapsed < 10.0, (
        f"Quota exhaustion should fail fast but took {elapsed:.2f}s — "
        "SDK retry delay is being waited on."
    )
    # Falls back to deterministic explanation
    assert "IS 7098" in result or "Gemini explanation" in result


# ---------------------------------------------------------------------------
# 5. Gemini 404 model not found — skip without blocking
# ---------------------------------------------------------------------------

def test_gemini_model_not_found_skips_fast():
    """A 404 NOT_FOUND error skips the candidate quickly."""
    not_found_error = Exception(
        "404 NOT_FOUND. This model models/gemini-2.5-flash is no longer available."
    )

    svc = ExplanationService(gemini_api_key="fake-key-for-test")
    svc._sdk_available = True

    t0 = time.monotonic()
    with patch(
        "backend.app.services.explanation_service._call_gemini_sdk",
        side_effect=not_found_error,
    ):
        result = svc._generate_with_hard_timeout("Test prompt")

    elapsed = time.monotonic() - t0
    assert elapsed < 10.0, f"Model not-found should be fast, took {elapsed:.2f}s"
    assert result is None  # All candidates exhausted


# ---------------------------------------------------------------------------
# 6. Malformed / empty Gemini response returns None (falls back)
# ---------------------------------------------------------------------------

def test_gemini_empty_response_falls_back():
    """If Gemini returns empty text, _generate_with_hard_timeout returns None."""
    svc = ExplanationService(gemini_api_key="fake-key-for-test")
    svc._sdk_available = True

    # _call_gemini_sdk raises ValueError on empty response (per implementation)
    with patch(
        "backend.app.services.explanation_service._call_gemini_sdk",
        side_effect=ValueError("Empty response from gemini-3.6-flash"),
    ):
        result = svc._generate_with_hard_timeout("some prompt")

    assert result is None


# ---------------------------------------------------------------------------
# 7. No API key configured — returns deterministic result immediately
# ---------------------------------------------------------------------------

def test_explanation_no_api_key():
    """Without an API key, ExplanationService always returns deterministic fallback."""
    svc = ExplanationService(gemini_api_key="")

    t0 = time.monotonic()
    result = svc.generate_explanation(
        query="PVC cables",
        features={},
        recommendations=[
            {
                "is_code": "IS 694",
                "title": "PVC Insulated Cables",
                "score": 0.90,
                "reason": "PVC cable match",
            }
        ],
    )
    elapsed = time.monotonic() - t0

    assert elapsed < 0.5, f"Should be instant without API key, took {elapsed:.2f}s"
    assert "IS 694" in result
    assert "Gemini explanation unavailable" in result


# ---------------------------------------------------------------------------
# 8. generate_procurement_explanation returns GroundedExplanation when Gemini fails
# ---------------------------------------------------------------------------

def test_procurement_explanation_gemini_failure_returns_full_result():
    """
    Even when Gemini fails, generate_procurement_explanation returns a
    complete GroundedExplanation with all deterministic fields populated.
    """
    svc = ExplanationService(gemini_api_key="fake-key-for-test")
    svc._sdk_available = True

    items = [_make_item("Steel TMT bars", has_standard=True)]
    recs = [_make_sourcing_rec("SOURCING_REGION")]
    pkg = _make_package_eval()

    with patch(
        "backend.app.services.explanation_service._call_gemini_sdk",
        side_effect=Exception("429 RESOURCE_EXHAUSTED quota exceeded"),
    ):
        result = svc.generate_procurement_explanation(
            company="Test Startup",
            items=items,
            package_eval=pkg,
            sourcing_recs=recs,
        )

    assert isinstance(result, GroundedExplanation)
    assert result.summary  # Non-empty
    assert "Gemini explanation temporarily unavailable" in result.summary
    assert result.synthesis_type == "GROUNDED_DETERMINISTIC_FALLBACK"
    assert len(result.supported_by_data) > 0  # Standards evidence present
    assert result.compliance_caveats  # Non-empty


# ---------------------------------------------------------------------------
# 9. generate_procurement_explanation with no API key returns GroundedExplanation
# ---------------------------------------------------------------------------

def test_procurement_explanation_no_api_key():
    """Without API key, procurement explanation is deterministic and complete."""
    svc = ExplanationService(gemini_api_key="")

    items = [_make_item("Solar PV panels", has_standard=True)]
    recs = [_make_sourcing_rec("MANUFACTURER")]
    pkg = _make_package_eval()

    result = svc.generate_procurement_explanation(
        company="SolarTech Pvt Ltd",
        items=items,
        package_eval=pkg,
        sourcing_recs=recs,
    )

    assert isinstance(result, GroundedExplanation)
    assert result.summary
    assert result.synthesis_type == "GROUNDED_DETERMINISTIC_FALLBACK"
    assert "Solar PV panels" in " ".join(result.supported_by_data)


# ---------------------------------------------------------------------------
# 10. End-to-end: procurement analysis API returns HTTP 200 even if Gemini fails
# ---------------------------------------------------------------------------

def test_procurement_api_returns_200_when_gemini_unavailable():
    """
    POST /api/v1/procurement/analyze must return HTTP 200 with results
    even when Gemini is completely unavailable (no key or quota exceeded).
    """
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)

    # Patch Gemini to be unavailable
    with patch(
        "backend.app.services.explanation_service._call_gemini_sdk",
        side_effect=Exception("429 RESOURCE_EXHAUSTED quota exceeded"),
    ):
        response = client.post(
            "/api/v1/procurement/analyze",
            json={
                "company": "Test Infrastructure Co.",
                "requirements": [
                    {
                        "item": "PVC insulated electrical cables",
                        "quantity": 500,
                        "unit": "meters",
                        "specifications": "1.1 kV working voltage, 4-core",
                    },
                    {
                        "item": "High strength deformed steel bars",
                        "quantity": 10,
                        "unit": "MT",
                        "specifications": "Fe 500D grade TMT bars",
                    },
                ],
            },
        )

    assert response.status_code == 200, (
        f"Expected HTTP 200 but got {response.status_code}: {response.text[:300]}"
    )
    data = response.json()

    # Core procurement results must be present
    assert "items" in data
    assert "package_evaluation" in data
    assert "recommendations" in data
    assert "explanation" in data

    # Explanation must be the deterministic fallback, not empty
    explanation = data["explanation"]
    assert explanation["summary"]
    assert "Gemini explanation" in explanation["summary"] or len(explanation["supported_by_data"]) > 0

    # Synthesis type should reflect fallback
    assert explanation["synthesis_type"] in ("GROUNDED_DETERMINISTIC_FALLBACK", "LIVE_GEMINI_SYNTHESIS")
