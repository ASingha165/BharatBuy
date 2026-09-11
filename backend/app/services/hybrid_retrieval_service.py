from typing import List, Dict, Any, Tuple, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.repositories.standards_repository import StandardsRepository
from backend.app.services.preprocessing_service import PreprocessingService
from backend.app.services.feature_service import FeatureService
from backend.app.services.baseline_model import BaselineRecommendationModel
from backend.app.services.bm25_service import BM25Service
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.reranker_service import RerankerService
from backend.app.services.graph_service import GraphService
from backend.app.models.responses import RecommendationResultItem

class HybridRetrievalService:
    """
    Unified Multi-Stage Hybrid Retrieval Engine:
    Stage 1: Candidate Generation via SQLite Repository (559 standards)
    Stage 2: BM25 Okapi lexical scoring + Semantic Embedding similarity + Baseline Feature weighting
    Stage 3: Score Fusion (Weighted Linear / Reciprocal Rank Fusion)
    Stage 4: CrossEncoder Deep Reranking (with graceful fallback)
    Stage 5: Knowledge Graph edge enrichment
    """

    def __init__(
        self,
        repository: StandardsRepository,
        preprocessing_service: Optional[PreprocessingService] = None,
        feature_service: Optional[FeatureService] = None,
        graph_service: Optional[GraphService] = None,
        bm25_service: Optional[BM25Service] = None,
        embedding_service: Optional[EmbeddingService] = None,
        reranker_service: Optional[RerankerService] = None
    ):
        self.repository = repository
        self.preprocessing = preprocessing_service or PreprocessingService()
        self.feature_service = feature_service or FeatureService(self.preprocessing)
        self.graph_service = graph_service or GraphService()
        self.baseline_model = BaselineRecommendationModel()

        self.bm25_service = bm25_service or BM25Service()
        self.embedding_service = embedding_service or EmbeddingService()
        self.reranker_service = reranker_service or RerankerService()
        
        self._indices_initialized = False

    def initialize_indices(self):
        """Pre-indexes standards into BM25 and Semantic Embedding engines."""
        if self._indices_initialized:
            return
        try:
            standards = self.repository.get_all_standards()
            if standards:
                self.bm25_service.index_standards(standards)
                self.embedding_service.initialize(standards)
                self.reranker_service.initialize()
                self._indices_initialized = True
                logger.info(f"Hybrid retrieval indices initialized with {len(standards)} Indian Standards.")
        except Exception as e:
            logger.warning(f"Partial failure initializing hybrid indices: {e}. Will rely on baseline fallback.")

    def retrieve_and_rank(self, query: str, top_k: int = 5) -> List[RecommendationResultItem]:
        if not query or not query.strip():
            return []

        # Ensure indices are ready
        if not self._indices_initialized:
            self.initialize_indices()

        all_standards = self.repository.get_all_standards()
        if not all_standards:
            return []

        # 1. Feature extraction
        features = self.feature_service.extract_features(query)

        # 2. Stage 1: Baseline Rule & Unit Scoring
        baseline_results = self.baseline_model.predict(
            query=query,
            features=features,
            candidates=all_standards,
            top_k=len(all_standards)
        )
        baseline_score_map: Dict[str, Tuple[float, str]] = {
            std["standard_id"]: (score, reason) for std, score, reason in baseline_results
        }

        # 3. Stage 2: BM25 Lexical Retrieval
        bm25_score_map: Dict[str, float] = {}
        try:
            bm25_results = self.bm25_service.search(query, top_k=50)
            for std, score in bm25_results:
                bm25_score_map[std["standard_id"]] = score
        except Exception as e:
            logger.debug(f"BM25 search skipped: {e}")

        # 4. Stage 3: Semantic Embedding Retrieval
        semantic_score_map: Dict[str, float] = {}
        try:
            semantic_results = self.embedding_service.search(query, top_k=50)
            for std, score in semantic_results:
                semantic_score_map[std["standard_id"]] = score
        except Exception as e:
            logger.debug(f"Semantic vector search skipped: {e}")

        # 5. Stage 4: Fusion of Retrieval Signals
        # Combined score = 0.40 * Baseline + 0.30 * BM25 + 0.30 * Semantic
        fused_candidates: List[Tuple[Dict[str, Any], float, str]] = []

        for std in all_standards:
            s_id = std["standard_id"]
            base_score, reason = baseline_score_map.get(s_id, (0.05, "Scope alignment"))
            bm25_sc = bm25_score_map.get(s_id, 0.0)
            sem_sc = semantic_score_map.get(s_id, 0.0)

            # If semantic or BM25 has signal, incorporate it
            fused_score = (base_score * 0.45) + (bm25_sc * 0.30) + (sem_sc * 0.25)
            # Ensure minimum floor
            final_fused = round(min(max(fused_score, base_score * 0.5), 0.98), 4)

            # Enrich reason if BM25 or Semantic showed high match
            enhanced_reason = reason
            if bm25_sc > 0.7:
                enhanced_reason += f" High textual BM25 correlation ({int(bm25_sc * 100)}%)."
            if sem_sc > 0.7:
                enhanced_reason += f" Semantic concept alignment ({int(sem_sc * 100)}%)."

            # Retain standards that have meaningful relevance
            if final_fused > 0.15 or base_score > 0.35:
                fused_candidates.append((std | {"hybrid_score": final_fused}, final_fused, enhanced_reason))

        fused_candidates.sort(key=lambda x: x[1], reverse=True)
        top_pool = fused_candidates[:max(top_k * 2, 10)]

        # 6. Stage 5: CrossEncoder Reranking on Top Candidates
        reranked_pool: List[Tuple[Dict[str, Any], float, str]] = []
        if self.reranker_service._is_ready:
            try:
                candidate_dicts = [item[0] for item in top_pool]
                reranked_tuples = self.reranker_service.rerank(query, candidate_dicts, top_k=top_k)
                
                # Map reranked scores back
                reranked_score_dict = {cand["standard_id"]: score for cand, score in reranked_tuples}
                for std, orig_score, reason in top_pool:
                    s_id = std["standard_id"]
                    if s_id in reranked_score_dict:
                        cross_score = reranked_score_dict[s_id]
                        blended_score = round(0.5 * orig_score + 0.5 * cross_score, 4)
                        reranked_pool.append((std, blended_score, reason))
                reranked_pool.sort(key=lambda x: x[1], reverse=True)
            except Exception as e:
                logger.warning(f"CrossEncoder reranking error: {e}. Utilizing fused results.")
                reranked_pool = top_pool[:top_k]
        else:
            reranked_pool = top_pool[:top_k]

        # 7. Knowledge Graph Enrichment
        final_items: List[RecommendationResultItem] = []
        for std, score, reason in reranked_pool[:top_k]:
            s_id = std["standard_id"]
            related = self.graph_service.get_related_standards(s_id)
            
            final_items.append(RecommendationResultItem(
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
            ))

        return final_items
