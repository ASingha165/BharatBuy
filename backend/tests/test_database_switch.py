import os
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.database import DatabaseManager
from backend.app.repositories.standards_repository import StandardsRepository
from backend.app.repositories.user_repository import UserRepository


client = TestClient(app)


def test_mode_a_sqlite_fallback():
    """MODE A: When DATABASE_URL is unset/empty, system runs on local SQLite."""
    manager = DatabaseManager(force_sqlite=True, sqlite_path=settings.DATABASE_PATH)
    assert manager.engine_name == "sqlite"
    assert manager.is_postgres is False
    assert manager.check_health() is True

    repo = StandardsRepository(manager=manager)
    assert repo.engine_name == "sqlite"
    assert repo.check_health() is True
    assert repo.get_total_count() == 559

    std = repo.get_standard_by_id("IS-7098-1")
    assert std is not None
    assert std["is_code"] == "IS 7098 (Part 1)"
    assert std["publication_year"] == 1988

    user_repo = UserRepository(manager=manager)
    assert user_repo.engine_name == "sqlite"
    user = user_repo.get_user_by_email("sin@game.dev")
    assert user is not None
    assert user["name"] == "Ankit Singha"


def test_mode_b_neon_postgresql():
    """MODE B: When DATABASE_URL is set, system connects to Neon PostgreSQL."""
    if not settings.DATABASE_URL:
        pytest.skip("DATABASE_URL not configured")

    manager = DatabaseManager(database_url=settings.DATABASE_URL)
    assert manager.engine_name == "postgresql"
    assert manager.is_postgres is True
    assert manager.check_health() is True

    repo = StandardsRepository(manager=manager)
    assert repo.engine_name == "postgresql"
    assert repo.check_health() is True
    assert repo.get_total_count() == 559

    std = repo.get_standard_by_id("IS-7098-1")
    assert std is not None
    assert std["is_code"] == "IS 7098 (Part 1)"
    assert std["publication_year"] == 1988

    user_repo = UserRepository(manager=manager)
    assert user_repo.engine_name == "postgresql"
    user = user_repo.get_user_by_email("sin@game.dev")
    assert user is not None
    assert user["name"] == "Ankit Singha"


def test_api_endpoints_work():
    """Verify common API endpoints return valid HTTP 200 responses."""
    # 1. Health check
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database"] is True
    assert data["total_standards"] == 559

    # 2. Recommendations
    res_rec = client.post("/api/v1/recommend", json={
        "query": "Procurement of 1.1 kV XLPE insulated cables for underground power distribution",
        "top_k": 5
    })
    assert res_rec.status_code == 200
    rec_data = res_rec.json()
    assert rec_data["total_found"] > 0
    assert any("7098" in r["is_code"] for r in rec_data["results"])

    # 3. Standard detail
    res_std = client.get("/api/v1/standards/IS-7098-1")
    assert res_std.status_code == 200
    assert res_std.json()["is_code"] == "IS 7098 (Part 1)"

    # 4. Sourcing sources
    res_src = client.get("/api/v1/procurement/sources")
    assert res_src.status_code == 200
    sources = res_src.json()
    assert len(sources) >= 17

    # 5. Graph
    res_graph = client.get("/api/v1/graph/IS-7098-1")
    assert res_graph.status_code == 200
    assert res_graph.json()["center_standard_id"] == "IS-7098-1"
