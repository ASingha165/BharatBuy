import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Indian Standards Intelligence Engine"
    API_V1_STR: str = "/api/v1"
    
    GEMINI_API_KEY: str = ""
    # Gemini API requires minimum deadline of 10s; 15s gives comfortable headroom.
    GEMINI_REQUEST_TIMEOUT_SECONDS: float = 15.0
    
    # Database Settings: if DATABASE_URL is set (PostgreSQL/Neon), it takes precedence over SQLite
    DATABASE_URL: Optional[str] = None
    DATABASE_PATH: str = "data/standards-database-v5.db"
    GRAPH_PATH: str = "data/standards-knowledge-graph-v5.json"
    
    MODEL_TYPE: str = "baseline"  # "baseline" or "custom"
    CUSTOM_MODEL_PATH: str = ""
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    PROCUREMENT_API_STR: str = "/api/procurement"
    TOP_K: int = 10
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "*"]
    
    # Phase 5: Demo Mode & Data Hardening
    BHARATBUY_DEMO_MODE: bool = False

    # Authentication & Session Settings
    ENABLE_LEGACY_AUTH: bool = False  # Production default False: requires Firebase Auth
    AUTH_SECRET_KEY: str = "bharatbuy-procurement-secret-key-dev-change-in-prod"
    AUTH_TOKEN_EXPIRE_DAYS: int = 7
    AUTH_COOKIE_NAME: str = "bharatbuy_session"
    FIREBASE_PROJECT_ID: str = "bharatbuy-d4b11"
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
