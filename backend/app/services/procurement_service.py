import uuid
from typing import Optional, List
from backend.app.core.logging import logger
from backend.app.core.config import settings
from backend.app.models.requests import ProcurementAnalysisRequest, ProcurementRequirementItem
from backend.app.models.responses import (
    ProcurementAnalysisResponse,
    ItemComplianceEvaluation,
    PackageEvaluation,
    SourcingRecommendationItem,
    MapPointItem,
    GroundedExplanation
)
from backend.app.services.normalization_service import NormalizationService
from backend.app.services.hybrid_retrieval_service import HybridRetrievalService
from backend.app.services.package_evaluation_service import PackageEvaluationService
from backend.app.services.sourcing_service import SourcingService
from backend.app.services.explanation_service import ExplanationService

class ProcurementService:
    """
    High-level orchestrator for end-to-end multi-item procurement analysis:
    Normalization -> Hybrid Retrieval -> Compliance Scoring -> Package Feasibility -> Sourcing -> Explanation.
    """

    def __init__(
        self,
        normalization_service: NormalizationService,
        hybrid_retrieval_service: HybridRetrievalService,
        package_evaluation_service: PackageEvaluationService,
        sourcing_service: SourcingService,
        explanation_service: ExplanationService
    ):
        self.normalization_service = normalization_service
        self.hybrid_retrieval_service = hybrid_retrieval_service
        self.package_evaluation_service = package_evaluation_service
        self.sourcing_service = sourcing_service
        self.explanation_service = explanation_service

    def analyze(self, request: ProcurementAnalysisRequest) -> ProcurementAnalysisResponse:
        req_id = f"PROC-{uuid.uuid4().hex[:8].upper()}"
        company = request.company.strip() or "Enterprise Buyer"
        logger.info(f"[PROCUREMENT] Analyzing procurement request {req_id} for company '{company}'")

        # 1. Extract / Parse Line Items
        raw_items: List[ProcurementRequirementItem] = list(request.requirements or [])
        if not raw_items and request.description and request.description.strip():
            logger.info(f"[PROCUREMENT] Parsing line items from natural language description...")
            raw_items = self.normalization_service.parse_natural_language_requirements(request.description)

        if not raw_items:
            logger.warning(f"[PROCUREMENT] No line items or description provided in request {req_id}")
            empty_pkg = self.package_evaluation_service.evaluate_package([])
            return ProcurementAnalysisResponse(
                request_id=req_id,
                company=company,
                model="hybrid-bm25-semantic",
                is_demo_mode=settings.BHARATBUY_DEMO_MODE,
                items=[],
                package_evaluation=empty_pkg,
                recommendations=[],
                map_points=[],
                explanation=GroundedExplanation(
                    summary="No procurement requirements were provided for analysis.",
                    supported_by_data=[],
                    inference_requires_verification=[],
                    compliance_caveats=[],
                    missing_information=["Requirements list and description are both empty."]
                )
            )

        logger.info(f"[PROCUREMENT] Evaluating {len(raw_items)} line items...")

        # 2. Normalize and Evaluate Each Item
        evaluated_items: List[ItemComplianceEvaluation] = []

        for idx, r in enumerate(raw_items, 1):
            item_id = f"ITEM-{idx:02d}"
            normalized = self.normalization_service.normalize_item(r, index=idx)

            # Formulate robust multi-token search query
            search_query_parts = [normalized.item_name]
            if normalized.specifications:
                search_query_parts.append(normalized.specifications)
            if normalized.inferred_standard_requirements:
                search_query_parts.append(" ".join(normalized.inferred_standard_requirements))

            query_str = " ".join(search_query_parts)

            # Retrieve & rank standards using hybrid engine
            top_k = request.top_k_per_item or 5
            matching_stds = self.hybrid_retrieval_service.retrieve_and_rank(query_str, top_k=top_k)

            # Evaluate item compliance
            item_eval = self.package_evaluation_service.evaluate_item_compliance(
                item_id=item_id,
                normalized=normalized,
                matching_standards=matching_stds
            )
            evaluated_items.append(item_eval)

        # 3. Sourcing Recommendations & Location Mapping
        sourcing_recs = self.sourcing_service.generate_recommendations(evaluated_items)
        map_points = self.sourcing_service.build_map_points(sourcing_recs)
        logger.info(f"[PROCUREMENT] Identified {len(sourcing_recs)} sourcing options ({len(map_points)} unique map coordinates).")

        # 4. Holistic Package Evaluation (with sourcing and verification metrics)
        package_eval = self.package_evaluation_service.evaluate_package(
            items=evaluated_items,
            sourcing_recs=sourcing_recs
        )
        logger.info(f"[PROCUREMENT] Package evaluation complete: readiness={package_eval.overall_readiness_score}% ({package_eval.readiness_level})")

        # 5. Grounded AI Explanation
        explanation = self.explanation_service.generate_procurement_explanation(
            company=company,
            items=evaluated_items,
            package_eval=package_eval,
            sourcing_recs=sourcing_recs
        )

        return ProcurementAnalysisResponse(
            request_id=req_id,
            company=company,
            model="hybrid-bm25-semantic",
            is_demo_mode=settings.BHARATBUY_DEMO_MODE,
            items=evaluated_items,
            package_evaluation=package_eval,
            recommendations=sourcing_recs,
            map_points=map_points,
            explanation=explanation
        )
