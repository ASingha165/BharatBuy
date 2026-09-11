from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_get_standard_details():
    response = client.get("/api/v1/standards/IS-694")
    assert response.status_code == 200
    data = response.json()
    assert data["standard_id"] == "IS-694"
    assert data["is_code"] == "IS 694"
    assert len(data["related_standards"]) > 0

def test_get_graph_data():
    response = client.get("/api/v1/graph/IS-694")
    assert response.status_code == 200
    data = response.json()
    assert data["center_standard_id"] == "IS-694"
    assert len(data["nodes"]) > 0
    assert len(data["edges"]) > 0
