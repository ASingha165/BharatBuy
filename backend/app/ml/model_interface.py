from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple

class RecommendationModel(ABC):
    """
    Abstract interface for Indian Standards Recommendation Models.
    Allows seamless swapping between BaselineRecommendationModel and CustomTrainedModel.
    """
    
    @abstractmethod
    def predict(
        self, 
        query: str, 
        features: Dict[str, Any], 
        candidates: List[Dict[str, Any]], 
        top_k: int = 10
    ) -> List[Tuple[Dict[str, Any], float, str]]:
        """
        Rank and score candidate Indian Standards.
        
        Args:
            query: The raw/normalized user query string.
            features: Structured features extracted from the query.
            candidates: List of standard metadata dictionaries from the database.
            top_k: Maximum number of ranked recommendations to return.
            
        Returns:
            List of tuples: (standard_dict, relevance_score_between_0_and_1, match_reason_description)
        """
        pass
