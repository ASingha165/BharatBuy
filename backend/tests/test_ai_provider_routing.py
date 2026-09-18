"""Regression tests for the optional Gemma/Gemini explanation routing layer."""

from unittest.mock import patch

from backend.app.core.config import settings
from backend.app.services.explanation_service import ExplanationService


def _recommendation():
    return [{
        "is_code": "IS 1786",
        "title": "High Strength Deformed Steel Bars",
        "score": 0.9,
        "reason": "Technical match from the deterministic engine",
    }]


def test_gemma_provider_initialization():
    service = ExplanationService(gemini_api_key="", gemma_api_key="gemma-test-key")
    service._gemma_sdk_available = True
    assert service.gemma_configured is True
    assert service.gemma_provider.name == "gemma"
    assert service.gemma_provider.model == settings.GEMMA_MODEL


def test_gemini_provider_initialization():
    service = ExplanationService(gemini_api_key="gemini-test-key", gemma_api_key="")
    service._sdk_available = True
    assert service.gemini_configured is True
    assert service.gemini_provider.name == "gemini"


def test_fast_task_prefers_gemma_without_calling_gemini():
    service = ExplanationService(gemini_api_key="gemini-key", gemma_api_key="gemma-key")
    service._sdk_available = True
    service._gemma_sdk_available = True

    with patch.object(service, "_generate_with_gemma_timeout", return_value="Fast Gemma summary") as gemma_call:
        with patch.object(service, "_generate_with_hard_timeout") as gemini_call:
            result = service.generate_explanation("TMT steel", {}, _recommendation())

    assert result == "Fast Gemma summary"
    gemma_call.assert_called_once()
    gemini_call.assert_not_called()
    assert service.last_provider == "gemma"


def test_complex_task_prefers_gemini():
    service = ExplanationService(gemini_api_key="gemini-key", gemma_api_key="gemma-key")
    service._sdk_available = True
    service._gemma_sdk_available = True

    with patch.object(service, "_generate_with_hard_timeout", return_value="Complex Gemini briefing") as gemini_call:
        with patch.object(service, "_generate_with_gemma_timeout") as gemma_call:
            result = service.generate_procurement_explanation(
                "Buyer", [], type("Package", (), {
                    "total_items": 0,
                    "overall_readiness_score": 0,
                    "readiness_level": "LOW",
                    "standards_coverage": 0,
                    "sourcing_coverage": 0,
                    "verification_coverage": 0,
                    "decision_status": "NOT_RECOMMENDED",
                    "decision_summary": None,
                })(), []
            )

    assert result.summary == "Complex Gemini briefing"
    gemini_call.assert_called_once()
    gemma_call.assert_not_called()
    assert result.ai_provider == "gemini"


def test_gemini_failure_falls_back_to_gemma_for_package():
    service = ExplanationService(gemini_api_key="gemini-key", gemma_api_key="gemma-key")
    service._sdk_available = True
    service._gemma_sdk_available = True

    package = type("Package", (), {
        "total_items": 0,
        "overall_readiness_score": 0,
        "readiness_level": "LOW",
        "standards_coverage": 0,
        "sourcing_coverage": 0,
        "verification_coverage": 0,
        "decision_status": "NOT_RECOMMENDED",
        "decision_summary": None,
    })()
    with patch.object(service, "_generate_with_hard_timeout", return_value=None):
        with patch.object(service, "_generate_with_gemma_timeout", return_value="Fallback Gemma briefing"):
            result = service.generate_procurement_explanation("Buyer", [], package, [])

    assert result.summary == "Fallback Gemma briefing"
    assert result.ai_provider == "gemma"
    assert result.synthesis_type == "LIVE_GEMMA_SYNTHESIS"


def test_both_providers_unavailable_use_deterministic_fallback():
    service = ExplanationService(gemini_api_key="", gemma_api_key="")
    result = service.generate_explanation("TMT steel", {}, _recommendation())
    assert result.startswith("Gemini explanation unavailable.")
    assert "IS 1786" in result
    assert service.last_provider == "deterministic_fallback"


def test_health_metadata_never_contains_api_keys():
    service = ExplanationService(gemini_api_key="secret-gemini", gemma_api_key="secret-gemma")
    service._sdk_available = True
    service._gemma_sdk_available = True
    assert "secret-gemini" not in repr(service.gemini_provider)
    assert "secret-gemma" not in repr(service.gemma_provider)
