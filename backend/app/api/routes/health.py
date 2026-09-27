from fastapi import APIRouter
from backend.app.models.responses import HealthStatusResponse
from backend.app.api.dependencies import repository, explanation_service
from backend.app.core.config import settings

router = APIRouter()

@router.get("/health", response_model=HealthStatusResponse)
def get_health_status():
    db_healthy = repository.check_health()
    total_stds = repository.get_total_count()
    gemini_ready = bool(explanation_service.gemini_configured)
    gemma_ready = bool(explanation_service.gemma_configured)
    gemini_usable = bool(explanation_service.gemini_available)
    gemma_usable = bool(gemma_ready)
    
    from backend.app.core.firebase import initialize_firebase_admin, FIREBASE_ADMIN_AVAILABLE
    fb_app = initialize_firebase_admin() if FIREBASE_ADMIN_AVAILABLE else None
    fb_ready = bool(fb_app is not None and settings.FIREBASE_PROJECT_ID)

    # Operational active provider resolution (never claims unconfigured provider is operational):
    if gemma_ready and gemma_usable:
        operational_fast = "gemma"
    elif gemini_ready and gemini_usable:
        operational_fast = "gemini"
    else:
        operational_fast = "deterministic_fallback"

    if gemini_ready and gemini_usable:
        operational_reasoning = "gemini"
    elif gemma_ready and gemma_usable:
        operational_reasoning = "gemma"
    else:
        operational_reasoning = "deterministic_fallback"

    return HealthStatusResponse(
        status="healthy" if db_healthy else "degraded",
        database=db_healthy,
        model_type=settings.MODEL_TYPE,
        total_standards=total_stds,
        gemini_configured=gemini_ready,
        gemini_available=gemini_usable,
        is_demo_mode=settings.BHARATBUY_DEMO_MODE,
        gemma_configured=gemma_ready,
        gemma_available=gemma_usable,
        active_fast_provider=operational_fast,
        active_reasoning_provider=operational_reasoning,
        configured_fast_provider=settings.AI_FAST_PROVIDER,
        configured_reasoning_provider=settings.AI_REASONING_PROVIDER,
        firebase_admin_configured=fb_ready,
        firebase_project_id=settings.FIREBASE_PROJECT_ID
    )
