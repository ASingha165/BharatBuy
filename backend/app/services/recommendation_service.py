from typing import List, Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.repositories.standards_repository import StandardsRepository
from backend.app.services.preprocessing_service import PreprocessingService
from backend.app.services.feature_service import FeatureService
from backend.app.services.graph_service import GraphService
from backend.app.services.explanation_service import ExplanationService
from backend.app.ml.model_interface import RecommendationModel
from backend.app.ml.model_loader import get_model
from backend.app.models.responses import RecommendationResponse, RecommendationResultItem

class RecommendationService:
    def __init__(
        self,
        repository: StandardsRepository,
        preprocessing_service: Optional[PreprocessingService] = None,
        feature_service: Optional[FeatureService] = None,
        graph_service: Optional[GraphService] = None,
        explanation_service: Optional[ExplanationService] = None,
        model: Optional[RecommendationModel] = None
    ):
        self.repository = repository
        self.preprocessing_service = preprocessing_service or PreprocessingService()
        self.feature_service = feature_service or FeatureService(self.preprocessing_service)
        self.graph_service = graph_service or GraphService()
        self.explanation_service = explanation_service or ExplanationService()
        self.model = model or get_model(settings.MODEL_TYPE)

    def recommend(self, query: str, top_k: int = 10) -> RecommendationResponse:
        logger.info(f"[ENGINE] Processing recommendation query: '{query}'")
        if not query or not query.strip():
            logger.warning("[ENGINE] Empty query provided.")
            return RecommendationResponse(
                query=query,
                model=settings.MODEL_TYPE,
                total_found=0,
                results=[],
                explanation="Procurement query is empty."
            )

        # 1. Feature Extraction
        features = self.feature_service.extract_features(query)
        logger.info(f"[ENGINE] Features extracted: products={features.get('products')}, materials={features.get('materials')}, units={features.get('units')}")

        # 2. Candidate Standards Retrieval from Repository
        all_standards = self.repository.get_all_standards()
        logger.info(f"[ENGINE] Retrieved {len(all_standards)} database candidates from SQLite repository.")

        # 3. Model Inference (BaselineRecommendationModel or CustomTrainedModel)
        logger.info(f"[ENGINE] Executing model inference with model_type='{settings.MODEL_TYPE}'...")
        top_k_results = self.model.predict(
            query=query,
            features=features,
            candidates=all_standards,
            top_k=top_k
        )
        logger.info(f"[ENGINE] Model prediction completed. Ranked top {len(top_k_results)} candidate standards.")

        # 4. Format Results & Enrich with Knowledge Graph Relationships
        final_items: List[RecommendationResultItem] = []
        raw_items_for_explanation: List[Dict[str, Any]] = []

        for std, score, reason in top_k_results:
            s_id = std["standard_id"]
            related = self.graph_service.get_related_standards(s_id)

            item = RecommendationResultItem(
                standard_id=s_id,
                is_code=std["is_code"],
                title=std["title"],
                department=std.get("department", "General"),
                scope_summary=std.get("scope_summary", ""),
                key_specifications=std.get("key_specifications", ""),
                testing_requirements=std.get("testing_requirements", ""),
                publication_year=std.get("publication_year"),
                status=std.get("status", "ACTIVE"),
                score=score,
                reason=reason,
                related_standards=related
            )
            final_items.append(item)
            raw_items_for_explanation.append(std | {"score": score, "reason": reason})

        # 5. Generate Explanation
        explanation = self.explanation_service.generate_explanation(
            query=query,
            features=features,
            recommendations=raw_items_for_explanation
        )

        logger.info(f"[ENGINE] Recommendation process finished. Returning {len(final_items)} standards.")
        return RecommendationResponse(
            query=query,
            model=settings.MODEL_TYPE,
            total_found=len(final_items),
            results=final_items,
            explanation=explanation
        )
