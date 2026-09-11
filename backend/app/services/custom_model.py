import os
import pickle
from typing import List, Dict, Any, Tuple, Optional
from backend.app.ml.model_interface import RecommendationModel
from backend.app.services.baseline_model import BaselineRecommendationModel
from backend.app.core.config import settings
from backend.app.core.logging import logger

class CustomTrainedModel(RecommendationModel):
    """
    Custom ML model interface for user's team-trained model.
    Loads trained model artifacts (e.g. Scikit-Learn, PyTorch, LightGBM, ONNX, Pickle).
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or settings.CUSTOM_MODEL_PATH or "models/custom_recommendation_model.pkl"
        self.model = None
        self.baseline_fallback = BaselineRecommendationModel()
        self._load_model()

    def _load_model(self):
        if not os.path.isabs(self.model_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            self.model_path = os.path.join(base_dir, self.model_path)

        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, "rb") as f:
                    self.model = pickle.load(f)
                logger.info(f"Successfully loaded custom trained ML model from '{self.model_path}'.")
            except Exception as e:
                logger.error(f"Failed to load custom model artifact at '{self.model_path}': {e}")
                self.model = None
        else:
            logger.warning(
                f"Custom model artifact not found at '{self.model_path}'. "
                f"App will use baseline fallback until custom model is trained and saved by team."
            )

    def predict(
        self, 
        query: str, 
        features: Dict[str, Any], 
        candidates: List[Dict[str, Any]], 
        top_k: int = 10
    ) -> List[Tuple[Dict[str, Any], float, str]]:
        if self.model and hasattr(self.model, "predict"):
            try:
                # Custom trained model inference hook
                predictions = self.model.predict(query=query, features=features, candidates=candidates, top_k=top_k)
                return predictions
            except Exception as e:
                logger.error(f"Error executing custom trained model prediction: {e}")

        # Fallback to baseline model if custom model is not loaded or raises error
        results = self.baseline_fallback.predict(query, features, candidates, top_k=top_k)
        updated_results = []
        for std, score, reason in results:
            custom_reason = f"[Custom ML Mode] {reason}" if not self.model else reason
            updated_results.append((std, score, custom_reason))
        return updated_results
