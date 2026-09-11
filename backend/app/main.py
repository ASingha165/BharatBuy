from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.logging import setup_logging, logger
from backend.app.api.dependencies import initialize_services
from backend.app.api.routes import health, recommendations, standards, graph, procurement, auth

setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs"
)

# Set up CORS middleware to support Next.js frontend (localhost:3000 / 127.0.0.1:3000)
cors_origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
def on_startup():
    logger.info("Starting up Indian Standards Intelligence Engine...")
    initialize_services()

# Include routers under /api/v1
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["Health"])
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(recommendations.router, prefix=settings.API_V1_STR, tags=["Recommendations"])
app.include_router(standards.router, prefix=settings.API_V1_STR, tags=["Standards"])
app.include_router(graph.router, prefix=settings.API_V1_STR, tags=["Knowledge Graph"])
app.include_router(procurement.router, prefix=f"{settings.API_V1_STR}/procurement", tags=["Procurement Analysis"])
# Direct alias route for /api/procurement
app.include_router(procurement.router, prefix=settings.PROCUREMENT_API_STR, tags=["Procurement Analysis (Direct Alias)"])


@app.get("/")
def root():
    return {
        "message": "Welcome to SIH26108 Indian Standards Intelligence & Procurement Engine API",
        "docs": f"{settings.API_V1_STR}/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
