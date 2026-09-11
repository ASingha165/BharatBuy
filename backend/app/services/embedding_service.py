from typing import List, Dict, Any, Tuple
import numpy as np
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.utils.text_normalizer import TextNormalizer

class EmbeddingService:
    def __init__(self):
        self.model = None
        self.model_name = settings.EMBEDDING_MODEL
        self.standards: List[Dict[str, Any]] = []
        self.embeddings: np.ndarray = None
        self._is_ready = False

    def initialize(self, standards: List[Dict[str, Any]]):
        self.standards = standards
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model '{self.model_name}'...")
            self.model = SentenceTransformer(self.model_name)
            
            corpus_texts = [
                f"{std.get('is_code', '')} - {std.get('title', '')}. Department: {std.get('department', '')}. Scope: {std.get('scope_summary', '')}. Specs: {std.get('key_specifications', '')}"
                for std in standards
            ]
            
            logger.info(f"Pre-computing embeddings for {len(standards)} standards...")
            self.embeddings = self.model.encode(corpus_texts, convert_to_numpy=True, normalize_embeddings=True)
            self._is_ready = True
            logger.info("Embedding service successfully initialized and cached.")
        except Exception as e:
            logger.warning(f"SentenceTransformers failed to initialize ('{e}'). Using TF-IDF fallback vectorizer.")
            self._initialize_fallback(standards)

    def _initialize_fallback(self, standards: List[Dict[str, Any]]):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.standards = standards
        corpus_texts = [
            f"{std.get('is_code', '')} {std.get('title', '')} {std.get('department', '')} {std.get('scope_summary', '')} {std.get('key_specifications', '')}"
            for std in standards
        ]
        self.model = TfidfVectorizer(stop_words='english', max_features=5000)
        self.embeddings = self.model.fit_transform(corpus_texts).toarray()
        # Normalize
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.embeddings = self.embeddings / norms
        self._is_ready = True
        logger.info("Fallback TF-IDF vectorizer ready.")

    def search(self, query: str, top_k: int = 20) -> List[Tuple[Dict[str, Any], float]]:
        if not self._is_ready or not self.standards or self.embeddings is None:
            return []
            
        normalized_query = TextNormalizer.normalize_query(query)
        
        try:
            if hasattr(self.model, 'encode'):
                query_vec = self.model.encode([normalized_query], convert_to_numpy=True, normalize_embeddings=True)[0]
            else:
                query_vec = self.model.transform([normalized_query]).toarray()[0]
                norm = np.linalg.norm(query_vec)
                if norm > 0:
                    query_vec = query_vec / norm

            similarities = np.dot(self.embeddings, query_vec)
            
            # Map score to [0, 1] range
            similarities = np.clip(similarities, 0.0, 1.0)
            
            results = []
            for idx, score in enumerate(similarities):
                if score > 0.05:
                    results.append((self.standards[idx], float(score)))
                    
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]
        except Exception as e:
            logger.error(f"Error during semantic vector search: {e}")
            return []
