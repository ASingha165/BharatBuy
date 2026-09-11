from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from backend.app.models.requests import RecommendationRequest
from backend.app.models.responses import RecommendationResponse
from backend.app.models.auth import UserResponse
from backend.app.api.routes.auth import get_current_user_optional
from backend.app.services.recommendation_service import RecommendationService
from backend.app.api.dependencies import get_recommendation_service
from backend.app.core.logging import logger

router = APIRouter()

@router.post("/recommend", response_model=RecommendationResponse)
def get_recommendations(
    payload: RecommendationRequest,
    service: RecommendationService = Depends(get_recommendation_service),
    current_user: Optional[UserResponse] = Depends(get_current_user_optional)
):
    logger.info(f"[API ROUTE] Recommendation request received: query='{payload.query}', top_k={payload.top_k}")
    if current_user:
        logger.info(f"[API ROUTE] Authenticated user: {current_user.email} (id: {current_user.id})")
    if not payload.query or len(payload.query.strip()) < 2:
        logger.warning("[API ROUTE] Request rejected: query string empty or too short.")
        raise HTTPException(status_code=400, detail="Query string cannot be empty or too short.")
        
    try:
        response = service.recommend(query=payload.query, top_k=payload.top_k)
        logger.info(f"[API ROUTE] Returning {response.total_found} recommendations (engine='{response.model}')")
        return response
    except Exception as e:
        logger.error(f"[API ROUTE] Internal error processing recommendation query '{payload.query}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal recommendation error: {str(e)}")
