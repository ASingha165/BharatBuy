from backend.app.repositories.standards_repository import StandardsRepository
from backend.app.services.preprocessing_service import PreprocessingService
from backend.app.services.feature_service import FeatureService
from backend.app.services.graph_service import GraphService
from backend.app.services.explanation_service import ExplanationService
from backend.app.services.recommendation_service import RecommendationService
from backend.app.services.normalization_service import NormalizationService
from backend.app.services.hybrid_retrieval_service import HybridRetrievalService
from backend.app.services.package_evaluation_service import PackageEvaluationService
from backend.app.services.sourcing_service import SourcingService
from backend.app.services.procurement_service import ProcurementService
from backend.app.services.bm25_service import BM25Service
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.reranker_service import RerankerService
from backend.app.ml.model_loader import get_model
from backend.app.core.config import settings
from backend.app.core.logging import logger

repository = StandardsRepository()
preprocessing_service = PreprocessingService()
feature_service = FeatureService(preprocessing_service)
graph_service = GraphService()
explanation_service = ExplanationService()
model_engine = get_model(settings.MODEL_TYPE)

bm25_service = BM25Service()
embedding_service = EmbeddingService()
reranker_service = RerankerService()

hybrid_retrieval_service = HybridRetrievalService(
    repository=repository,
    preprocessing_service=preprocessing_service,
    feature_service=feature_service,
    graph_service=graph_service,
    bm25_service=bm25_service,
    embedding_service=embedding_service,
    reranker_service=reranker_service
)

normalization_service = NormalizationService(
    preprocessing_service=preprocessing_service,
    feature_service=feature_service
)

from backend.app.services.evidence_service import EvidenceService

evidence_service = EvidenceService()
package_evaluation_service = PackageEvaluationService()
sourcing_service = SourcingService(evidence_service=evidence_service)

procurement_service = ProcurementService(
    normalization_service=normalization_service,
    hybrid_retrieval_service=hybrid_retrieval_service,
    package_evaluation_service=package_evaluation_service,
    sourcing_service=sourcing_service,
    explanation_service=explanation_service
)

recommendation_service = RecommendationService(
    repository=repository,
    preprocessing_service=preprocessing_service,
    feature_service=feature_service,
    graph_service=graph_service,
    explanation_service=explanation_service,
    model=model_engine
)

def initialize_services():
    logger.info("Initializing SIH26108 system services...")
    total_count = repository.get_total_count()
    logger.info(f"Connected to {repository.engine_name.upper()} repository with {total_count} Indian Standards.")
    logger.info(f"Active Recommendation Engine: {settings.MODEL_TYPE.upper()}")
    hybrid_retrieval_service.initialize_indices()

def get_repository() -> StandardsRepository:
    return repository

def get_recommendation_service() -> RecommendationService:
    return recommendation_service

def get_procurement_service() -> ProcurementService:
    return procurement_service

def get_sourcing_service() -> SourcingService:
    return sourcing_service

def get_evidence_service() -> EvidenceService:
    return evidence_service

from backend.app.repositories.user_repository import UserRepository
from backend.app.services.auth_service import AuthService

user_repository = UserRepository()
auth_service = AuthService(user_repo=user_repository)

def get_user_repository() -> UserRepository:
    return user_repository

def get_auth_service() -> AuthService:
    return auth_service

def get_graph_service() -> GraphService:
    return graph_service
