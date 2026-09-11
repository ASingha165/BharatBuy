from typing import List, Dict, Any, Tuple
from rank_bm25 import BM25Okapi
from backend.app.utils.text_normalizer import TextNormalizer
from backend.app.core.logging import logger

class BM25Service:
    def __init__(self):
        self.bm25: BM25Okapi = None
        self.standards: List[Dict[str, Any]] = []
        self.corpus_tokens: List[List[str]] = []

    def index_standards(self, standards: List[Dict[str, Any]]):
        self.standards = standards
        self.corpus_tokens = []
        
        for std in standards:
            text_corpus = f"{std.get('is_code', '')} {std.get('title', '')} {std.get('department', '')} {std.get('scope_summary', '')} {std.get('key_specifications', '')} {std.get('testing_requirements', '')}"
            tokens = TextNormalizer.tokenize(text_corpus)
            self.corpus_tokens.append(tokens)
            
        if self.corpus_tokens:
            self.bm25 = BM25Okapi(self.corpus_tokens)
            logger.info(f"Indexed {len(standards)} standards into BM25 engine.")

    def search(self, query: str, top_k: int = 20) -> List[Tuple[Dict[str, Any], float]]:
        if not self.bm25 or not self.standards:
            return []
            
        query_tokens = TextNormalizer.tokenize(query)
        if not query_tokens:
            return []
            
        raw_scores = self.bm25.get_scores(query_tokens)
        max_score = max(raw_scores) if len(raw_scores) > 0 and max(raw_scores) > 0 else 1.0
        
        # Sort and retrieve candidates
        scored_results = []
        for idx, score in enumerate(raw_scores):
            if score > 0:
                normalized_score = float(score / max_score)
                scored_results.append((self.standards[idx], normalized_score))
                
        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results[:top_k]
