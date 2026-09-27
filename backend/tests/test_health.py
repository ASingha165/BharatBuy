from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["database"] is True
    assert data["total_standards"] > 0
    assert "firebase_admin_configured" in data
    assert data["firebase_project_id"] == "bharatbuy-d4b11"

