from fastapi import APIRouter
from backend.app.models.responses import HealthStatusResponse
from backend.app.api.dependencies import repository, explanation_service
from backend.app.core.config import settings

router = APIRouter()

@router.get("/health", response_model=HealthStatusResponse)
def get_health_status():
    db_healthy = repository.check_health()
    total_stds = repository.get_total_count()
    gemini_ready = explanation_service.gemini_configured
    gemma_ready = explanation_service.gemma_configured
    
    return HealthStatusResponse(
        status="healthy" if db_healthy else "degraded",
        database=db_healthy,
        model_type=settings.MODEL_TYPE,
        total_standards=total_stds,
        gemini_configured=gemini_ready,
        gemma_configured=gemma_ready,
        active_fast_provider=settings.AI_FAST_PROVIDER,
        active_reasoning_provider=settings.AI_REASONING_PROVIDER,
        is_demo_mode=settings.BHARATBUY_DEMO_MODE
    )
