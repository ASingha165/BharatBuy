from typing import List, Dict, Any, Tuple
from backend.app.core.config import settings
from backend.app.core.logging import logger

class RerankerService:
    def __init__(self):
        self.model = None
        self.model_name = settings.RERANKER_MODEL
        self._is_ready = False

    def initialize(self):
        try:
            from sentence_transformers import CrossEncoder
            logger.info(f"Loading Cross-Encoder model '{self.model_name}'...")
            self.model = CrossEncoder(self.model_name)
            self._is_ready = True
            logger.info("Cross-Encoder reranker initialized successfully.")
        except Exception as e:
            logger.warning(f"Cross-Encoder initialization skipped ('{e}'). Will use hybrid score reranking.")
            self._is_ready = False

    def rerank(self, query: str, candidates: List[Dict[str, Any]], top_k: int = 10) -> List[Tuple[Dict[str, Any], float]]:
        if not candidates:
            return []
            
        if not self._is_ready or not self.model:
            # Fallback: maintain hybrid ranking order
            return [(cand, cand.get("hybrid_score", 0.5)) for cand in candidates[:top_k]]
            
        try:
            pairs = [
                (query, f"{cand.get('is_code', '')}: {cand.get('title', '')}. Scope: {cand.get('scope_summary', '')}")
                for cand in candidates
            ]
            scores = self.model.predict(pairs)
            
            # Normalize logits to [0, 1] range using sigmoid or min-max
            import numpy as np
            sigmoids = 1 / (1 + np.exp(-scores))
            
            reranked = []
            for cand, score in zip(candidates, sigmoids):
                reranked.append((cand, float(score)))
                
            reranked.sort(key=lambda x: x[1], reverse=True)
            return reranked[:top_k]
        except Exception as e:
            logger.error(f"Error during Cross-Encoder reranking: {e}")
            return [(cand, cand.get("hybrid_score", 0.5)) for cand in candidates[:top_k]]
