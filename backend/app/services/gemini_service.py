"""
GeminiService: Legacy standalone Gemini explanation helper used by the IS recommendation endpoint.
Delegates to ExplanationService's _generate_with_hard_timeout internally.

This module is preserved for backward compatibility with any existing references.
New code should use ExplanationService directly.
"""
from typing import List, Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger


class GeminiService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self._sdk_available = False
        self._initialize()

    def _initialize(self):
        if not self.api_key:
            logger.info("GEMINI_API_KEY is not set. Grounded explanations will use structured template engine fallback.")
            return

        try:
            import google.genai  # noqa: F401
            self._sdk_available = True
            logger.info("GeminiService initialized with google.genai SDK.")
        except ImportError:
            logger.warning("google.genai not installed. GeminiService will use deterministic fallback.")

    def generate_explanation(self, query: str, top_results: List[Dict[str, Any]]) -> str:
        if not top_results:
            return "No applicable Indian Standards were found in the database for the given procurement requirement."

        # Format grounded evidence context
        evidence_lines = []
        for idx, res in enumerate(top_results[:5], 1):
            is_code = res.get("is_code", "")
            title = res.get("title", "")
            dept = res.get("department", "")
            scope = res.get("scope_summary", "")
            specs = res.get("key_specifications", "")
            tests = res.get("testing_requirements", "")
            score = res.get("score", 0.0)

            evidence_lines.append(
                f"Candidate #{idx}:\n"
                f"- Code: {is_code} (ID: {res.get('standard_id', '')})\n"
                f"- Title: {title}\n"
                f"- Department: {dept}\n"
                f"- Retrieval Confidence Score: {score:.3f}\n"
                f"- Scope: {scope}\n"
                f"- Specifications: {specs}\n"
                f"- Testing Requirements: {tests}\n"
            )

        evidence_text = "\n".join(evidence_lines)

        prompt = f"""
You are the Official Indian Standards Procurement Intelligence Assistant.
Analyze the following procurement requirement and explain strictly using the supplied Indian Standards evidence why these standards apply.

CRITICAL INSTRUCTIONS:
1. Do not invent Indian Standards, IS numbers, requirements, testing procedures, certification rules, or technical facts that are not present in the supplied evidence.
2. Base your technical justification ONLY on the provided candidate standards below.
3. Highlight mandatory testing and quality parameters mentioned in the evidence.
4. If the supplied evidence is insufficient or partially matches, clearly state the limitations.

PROCUREMENT REQUIREMENT:
"{query}"

SUPPLIED EVIDENCE (ACTIVE INDIAN STANDARDS DATASET):
{evidence_text}

Provide a concise, professional technical explanation for procurement officers (3-4 paragraphs) breaking down:
- Primary applicable Indian Standard(s) and why they match the voltage/material/structural requirement
- Key mandatory testing and quality compliance parameters
- Inter-standard testing or material dependencies if present in the evidence.
"""

        if self.api_key and self._sdk_available:
            try:
                from backend.app.services.explanation_service import (  # noqa: PLC0415
                    _call_gemini_sdk,
                    GEMINI_MODEL_CANDIDATES,
                    GEMINI_REQUEST_TIMEOUT_SECONDS,
                )
                import concurrent.futures

                for candidate in GEMINI_MODEL_CANDIDATES:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(
                            _call_gemini_sdk,
                            self.api_key,
                            candidate,
                            prompt,
                            GEMINI_REQUEST_TIMEOUT_SECONDS,
                        )
                        try:
                            text = future.result(timeout=GEMINI_REQUEST_TIMEOUT_SECONDS + 1.0)
                            if text:
                                return text
                        except Exception as exc:
                            err = str(exc)[:160]
                            logger.warning(f"GeminiService candidate '{candidate}' failed: {err}")
                            continue
            except Exception as e:
                logger.error(f"GeminiService explanation generation failed: {e}")

        # Grounded Deterministic Template Fallback
        primary = top_results[0]
        explanation = "### Grounded Procurement Intelligence Summary\n\n"
        explanation += (
            f"Based on the official BIS dataset, **{primary.get('is_code')}** "
            f"({primary.get('title')}) is recommended as the primary standard for this requirement (*{query}*).\n\n"
        )
        explanation += "**Technical Justification**:\n"
        explanation += f"- **Applicability**: {primary.get('scope_summary')}\n"
        explanation += f"- **Key Specifications**: {primary.get('key_specifications')}\n"
        explanation += f"- **Quality & Testing Compliance**: {primary.get('testing_requirements')}\n\n"

        if len(top_results) > 1:
            explanation += "**Complementary & Supporting Standards**:\n"
            for sec in top_results[1:4]:
                explanation += f"- **{sec.get('is_code')}** — {sec.get('title')} (Department: {sec.get('department')})\n"

        return explanation
