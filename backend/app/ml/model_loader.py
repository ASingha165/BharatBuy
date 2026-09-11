from typing import Optional
from backend.app.ml.model_interface import RecommendationModel
from backend.app.services.baseline_model import BaselineRecommendationModel
from backend.app.services.custom_model import CustomTrainedModel
from backend.app.core.config import settings
from backend.app.core.logging import logger

def get_model(model_type: Optional[str] = None) -> RecommendationModel:
    selected_type = (model_type or settings.MODEL_TYPE or "baseline").lower()
    
    if selected_type == "custom":
        logger.info("Initializing CustomTrainedModel interface...")
        return CustomTrainedModel()
    else:
        logger.info("Initializing BaselineRecommendationModel...")
        return BaselineRecommendationModel()
