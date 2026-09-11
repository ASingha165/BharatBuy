"""
ExplanationService: Grounded AI explainability layer for BharatBuy procurement analysis.

Uses the google-genai SDK (google.genai >= 2.x) with a strict thread-level hard timeout
so that Gemini quota exhaustion, network delays, or model unavailability can NEVER
cause the procurement engine to hang indefinitely.

Architecture guarantee:
  - Gemini is an OPTIONAL EXPLAINABILITY LAYER only.
  - If Gemini fails, times out, or is unavailable, the engine returns the full
    deterministic/retrieval-based procurement result with a safe fallback explanation.
  - The hard timeout (GEMINI_HARD_TIMEOUT_SECONDS) is enforced at the OS thread level
    via concurrent.futures, preventing SDK-internal retries from blocking the response.
"""

from __future__ import annotations

import concurrent.futures
from typing import List, Dict, Any, Optional

from backend.app.core.config import settings
from backend.app.core.logging import logger

# Hard outer timeout (seconds) for the entire Gemini call including internal SDK retries.
# Must be comfortably under the frontend Axios timeout (120s) while allowing one good call.
GEMINI_HARD_TIMEOUT_SECONDS = 30.0

# Per-model HTTP request timeout passed to the SDK.
# Gemini API requires a minimum deadline of 10s; 15s gives comfortable headroom.
# Configurable via GEMINI_REQUEST_TIMEOUT_SECONDS in .env (read from settings at call-time).
GEMINI_REQUEST_TIMEOUT_SECONDS: float = 15.0  # default; overridden by settings at call-time

# Model candidates in preference order (fast, cost-efficient flash models).
# gemini-2.5-flash-lite and gemini-2.5-flash return 404 on this project's API key scope.
GEMINI_MODEL_CANDIDATES = [
    "gemini-3.6-flash",
    "gemini-flash-latest",
]


def _call_gemini_sdk(api_key: str, model: str, prompt: str, timeout: float) -> str:
    """
    Single blocking SDK call to google.genai. Runs inside a ThreadPoolExecutor worker.
    Raises immediately on 429/quota errors (no retry). Returns text on success.
    Raises on any SDK error so the caller can try the next candidate.
    """
    import google.genai as genai  # noqa: PLC0415
    import google.genai.errors as genai_errors  # noqa: PLC0415

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                http_options=genai.types.HttpOptions(timeout=int(timeout * 1000)),
            ),
        )
        text = getattr(response, "text", None) or ""
        if text and text.strip():
            return text.strip()
        raise ValueError(f"Empty response from {model}")
    except genai_errors.ClientError as e:
        # 429 = quota exceeded, 404 = model not found — surface immediately, no retry
        raise


class ExplanationService:
    """
    Builds grounded procurement explanations with optional Gemini AI enrichment.

    Gemini is strictly optional. All public methods always return a complete
    GroundedExplanation object regardless of Gemini availability.
    """

    def __init__(self, gemini_api_key: Any = None):
        # Accept None or a sentinel object for testing
        if gemini_api_key is None or isinstance(gemini_api_key, str):
            self.api_key = gemini_api_key if isinstance(gemini_api_key, str) else settings.GEMINI_API_KEY
        else:
            # Sentinel object passed from legacy constructor call
            self.api_key = settings.GEMINI_API_KEY

        self.api_key = (self.api_key or "").strip()
        self._sdk_available = False
        self.active_model_name: Optional[str] = None

        if self.api_key:
            try:
                import google.genai  # noqa: F401
                self._sdk_available = True
                logger.info("[ExplanationService] google.genai SDK available. Gemini explainability enabled.")
            except ImportError:
                logger.warning("[ExplanationService] google.genai not installed. Gemini disabled.")

    # ------------------------------------------------------------------
    # Internal: bounded multi-candidate Gemini generation
    # ------------------------------------------------------------------

    def _generate_with_hard_timeout(self, prompt: str) -> Optional[str]:
        """
        Attempts generation across GEMINI_MODEL_CANDIDATES.

        Uses a ThreadPoolExecutor with a hard wall-clock timeout so that
        SDK-internal retry delays (e.g. 34-second 429 retry intervals) can
        NEVER cause the procurement response to block past GEMINI_HARD_TIMEOUT_SECONDS.

        Returns the generated text string, or None if all candidates fail or timeout.
        """
        if not self.api_key or not self._sdk_available:
            return None

        remaining_budget = GEMINI_HARD_TIMEOUT_SECONDS

        for candidate in GEMINI_MODEL_CANDIDATES:
            if remaining_budget <= 0:
                logger.warning("[ExplanationService] Gemini hard timeout budget exhausted — using fallback.")
                break

            # Use settings value at call-time so .env overrides take effect without restart
            request_timeout = settings.GEMINI_REQUEST_TIMEOUT_SECONDS
            call_timeout = min(request_timeout, remaining_budget)

            import time
            t_start = time.monotonic()

            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            future = executor.submit(
                _call_gemini_sdk,
                self.api_key,
                candidate,
                prompt,
                call_timeout,
            )
            try:
                text = future.result(timeout=call_timeout + 1.0)
                elapsed = time.monotonic() - t_start
                self.active_model_name = candidate
                logger.info(f"[ExplanationService] Gemini '{candidate}' succeeded in {elapsed:.2f}s.")
                executor.shutdown(wait=False)
                return text
            except concurrent.futures.TimeoutError:
                elapsed = time.monotonic() - t_start
                future.cancel()
                # shutdown(wait=False) abandons the stuck worker thread immediately
                # instead of blocking until it finishes (which could be 999s).
                executor.shutdown(wait=False)
                logger.warning(
                    f"[ExplanationService] Gemini '{candidate}' hard-timeout after {elapsed:.2f}s — trying next candidate."
                )
            except Exception as exc:
                elapsed = time.monotonic() - t_start
                err_msg = str(exc)[:160]
                executor.shutdown(wait=False)
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower():
                    # Quota exceeded — log and skip; do NOT wait for the retryDelay
                    logger.warning(
                        f"[ExplanationService] Gemini '{candidate}' quota exceeded ({elapsed:.2f}s) — skipping."
                    )
                elif "404" in err_msg or "NOT_FOUND" in err_msg:
                    logger.warning(
                        f"[ExplanationService] Gemini '{candidate}' model not found ({elapsed:.2f}s) — skipping."
                    )
                else:
                    logger.warning(
                        f"[ExplanationService] Gemini '{candidate}' failed ({elapsed:.2f}s): {err_msg}"
                    )

            remaining_budget -= (time.monotonic() - t_start)

        logger.info("[ExplanationService] All Gemini candidates exhausted — using deterministic fallback.")
        return None

    # ------------------------------------------------------------------
    # Public: IS recommendation explanation (single-query path)
    # ------------------------------------------------------------------

    def generate_explanation(
        self,
        query: str,
        features: Dict[str, Any],
        recommendations: List[Dict[str, Any]],
    ) -> str:
        if not recommendations:
            return "No matching Indian Standards were found for the provided procurement specification."

        top_std = recommendations[0]
        top_code = top_std.get("is_code", "IS standard")
        top_title = top_std.get("title", "")
        top_reason = top_std.get("reason", "")

        # 1. Deterministic grounded explanation (always computed)
        lines = [
            f"Primary Recommendation: {top_code} - {top_title}.",
            f"Match Rationale: {top_reason}",
        ]
        if len(recommendations) > 1:
            lines.append(
                f"Secondary supporting standard identified: {recommendations[1].get('is_code', '')} - "
                f"{recommendations[1].get('title', '')}."
            )
        deterministic_summary = " ".join(lines)

        # 2. Optional Gemini enrichment
        if self.api_key and self._sdk_available:
            context = f"Procurement Query: '{query}'\nExtracted Features: {features}\nRecommended Standards:\n"
            for r in recommendations[:3]:
                context += (
                    f"- {r.get('is_code')}: {r.get('title')} "
                    f"(Score: {r.get('score')}, Reason: {r.get('reason')})\n"
                )
            prompt = (
                "You are an expert Indian Standards (BIS) procurement technical advisor for BharatBuy. "
                "CRITICAL GROUNDING RULES:\n"
                "1. Based ONLY on the provided procurement query and recommended standards above, "
                "provide a concise 2-3 sentence grounded explanation on why these Indian Standards apply.\n"
                "2. Do NOT invent standards, IS numbers, testing rules, or facts not in the context.\n"
                "3. STATIC EVIDENCE != CURRENT VERIFICATION: State that live vendor CML validity requires verification.\n"
                "4. Do NOT approve purchases autonomously; decision remains buyer-controlled.\n\n"
                f"{context}"
            )
            generated = self._generate_with_hard_timeout(prompt)
            if generated:
                return generated

        return (
            "Gemini explanation unavailable. The recommendation below is based on retrieved standards "
            f"and registered source evidence.\n\n{deterministic_summary}"
        )

    # ------------------------------------------------------------------
    # Public: Full procurement package explanation
    # ------------------------------------------------------------------

    def generate_procurement_explanation(
        self,
        company: str,
        items: List[Any],
        package_eval: Any,
        sourcing_recs: List[Any],
    ) -> Any:
        from backend.app.models.responses import GroundedExplanation  # noqa: PLC0415

        # 1. Build deterministic evidence lists (always runs)
        supported_data: List[str] = []
        inferences: List[str] = []
        caveats: List[str] = []
        missing_info: List[str] = []

        for itm in items:
            p_std = itm.primary_standard
            if p_std:
                supported_data.append(
                    f"[SUPPORTED BY DATABASE] [SUPPORTED BY EVIDENCE] Item '{itm.item_name}': "
                    f"Governed by {p_std.is_code} ({p_std.title}) with mandated testing clauses: "
                    f"{p_std.testing_requirements}."
                )
                if itm.is_mandatory_certification:
                    caveats.append(
                        f"[REQUIRES VERIFICATION] Statutory Mandate for '{itm.item_name}': "
                        f"Requires valid {itm.applicable_scheme} certification under BIS Quality Control Orders."
                    )
            else:
                inferences.append(
                    f"[INFERRED FROM MATCHING] [INFERRED] Item '{itm.item_name}': "
                    f"No direct standard match above threshold; requires technical verification against allied standards."
                )

            if itm.missing_parameters:
                missing_info.extend([f"'{itm.item_name}': {p}" for p in itm.missing_parameters])

        for rec in sourcing_recs[:5]:
            source_name = getattr(rec, "source_name", None) or getattr(rec, "supplier_name", "Unknown Source")
            st_type = getattr(rec, "source_type", "UNKNOWN")
            v_stat = getattr(rec, "verification_status", "UNKNOWN")
            bis_status = getattr(rec, "bis_certification_status", "REQUIRES_LIVE_VERIFICATION")
            trust_lvl = getattr(rec, "trust_level", "MODERATE")
            loc = rec.location
            loc_str = (
                f"{loc.city}, {loc.state}" if hasattr(loc, "city") else str(loc)
            )

            if v_stat == "CONFIRMED" or bis_status == "CONFIRMED":
                supported_data.append(
                    f"[SUPPORTED BY EVIDENCE] Manually Verified Source: '{source_name}' ({loc_str}) "
                    f"confirmed on official BIS portal by buyer."
                )
            elif st_type == "MANUFACTURER":
                ev_preview = (rec.verification_evidence or [])[:2]
                supported_data.append(
                    f"[SUPPORTED BY DATABASE] [SUPPORTED BY EVIDENCE] Documented Enterprise "
                    f"(Requires Live Verification): '{source_name}' ({loc_str}) — "
                    f"Trust: {trust_lvl}, Status: {bis_status}. "
                    f"Documented evidence: {'; '.join(ev_preview)}."
                )
                caveats.append(
                    f"[REQUIRES VERIFICATION] License Validity Check: Live operational verification required "
                    f"on official BIS portal (manakonline.in) for '{source_name}' before buyer approval."
                )
            elif st_type == "SOURCING_REGION":
                inferences.append(
                    f"[INFERRED FROM MATCHING] [INFERRED] Sourcing Region: '{source_name}' ({loc_str}) "
                    f"has industrial manufacturing cluster capacity for "
                    f"{', '.join(rec.supported_items)}. No supplier-level CML attached."
                )
            else:
                caveats.append(
                    f"[REQUIRES VERIFICATION] Channel Supplier: '{source_name}' requires vendor submission "
                    f"of original manufacturer test certificate and active BIS CML license."
                )

        det_score = getattr(package_eval, "decision_status", None) or getattr(
            package_eval, "decision_summary", None
        )
        det_decision = (
            det_score.decision_status
            if hasattr(det_score, "decision_status")
            else str(det_score or "READY_WITH_VERIFICATION")
        )
        summary_text = (
            f"Procurement Intelligence Package for {company}: Evaluated {package_eval.total_items} line items "
            f"with an overall readiness score of {package_eval.overall_readiness_score}% "
            f"({package_eval.readiness_level} readiness, Decision: {det_decision}). "
            f"Standards coverage stands at {int(package_eval.standards_coverage * 100)}%, "
            f"Sourcing coverage at {int(package_eval.sourcing_coverage * 100)}%, "
            f"and Documented Manufacturer Record coverage at {int(package_eval.verification_coverage * 100)}%."
        )

        # 2. Optional Gemini enrichment with hard timeout
        gemini_success = False
        synthesis_type = "GROUNDED_DETERMINISTIC_FALLBACK"

        if self.api_key and self._sdk_available:
            all_evidence_lines: List[str] = []
            for rec in sourcing_recs[:4]:
                ev_recs = getattr(rec, "evidence_records", [])
                for ev in ev_recs[:3]:
                    fresh = getattr(ev, "freshness_state", "UNKNOWN")
                    meth = getattr(ev, "verification_method", "REGISTRY")
                    all_evidence_lines.append(
                        f"- [{ev.evidence_type}] {ev.title} "
                        f"(Status: {ev.verification_status}, Method: {meth}, Freshness: {fresh}): "
                        f"{ev.supports_claim}"
                    )

            prompt = f"""You are the Senior BIS Procurement Compliance & Evidence Officer for BharatBuy.
Analyze the following evaluated procurement package for company '{company}'.

CRITICAL SAFETY & INTEGRITY RULES (STRICT COMPLIANCE MANDATED):
1. NEVER invent BIS standards, IS numbers, CML license numbers, laboratory accreditations, prices, stock levels, delivery lead times, or government authorizations.
2. NEVER claim 'Currently BIS certified', 'Valid CML', 'Active CRS', or 'Certified Supplier' unless evidence explicitly confirms it.
3. NEVER upgrade UNKNOWN -> VERIFIED, or REQUIRES_VERIFICATION -> CONFIRMED.
4. STATIC EVIDENCE != CURRENT VERIFICATION: Static registry evidence or historical CML records require live portal audit before contract award.
5. SOURCE != REGION_ONLY: Sourcing regions/corridors are geographic manufacturing clusters, NOT certified manufacturers or suppliers.
6. NO AUTONOMOUS PURCHASE APPROVAL: AI analysis provides evidence-backed decision support. Final decision is strictly 'Procurement-ready for buyer approval'.
7. For every factual claim, use ONLY the supplied evidence below.
8. Structure your response into three clear sections: [SUPPORTED BY EVIDENCE / DATABASE], [INFERRED FROM MATCHING], [REQUIRES VERIFICATION]

RETRIEVED BIS & SOURCING EVIDENCE:
{chr(10).join(supported_data)}
{chr(10).join(all_evidence_lines)}

INFERRED CLAIMS:
{chr(10).join(inferences) if inferences else "None."}

STATUTORY CAVEATS & VERIFICATION REQUIREMENTS:
{chr(10).join(caveats) if caveats else "None."}

MISSING PARAMETERS:
{chr(10).join(missing_info) if missing_info else "None."}

Provide a grounded, structured technical briefing following the three-tier format.
"""

            generated_briefing = self._generate_with_hard_timeout(prompt)
            if generated_briefing:
                summary_text = generated_briefing
                gemini_success = True
                synthesis_type = "LIVE_GEMINI_SYNTHESIS"

        if not gemini_success:
            summary_text = (
                "Gemini explanation temporarily unavailable. "
                "The recommendation below is based on retrieved standards and registered source evidence.\n\n"
                + summary_text
            )

        return GroundedExplanation(
            summary=summary_text,
            supported_by_data=supported_data,
            inference_requires_verification=(
                inferences if inferences else ["All line items mapped directly to retrieved Indian Standards."]
            ),
            compliance_caveats=(
                caveats if caveats else ["Verify vendor BIS mark license validity on manakonline.in prior to contract award."]
            ),
            missing_information=(
                missing_info if missing_info else ["No critical engineering parameters missing from submission."]
            ),
            synthesis_type=synthesis_type,
        )
