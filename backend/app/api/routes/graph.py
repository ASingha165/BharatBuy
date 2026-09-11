from fastapi import APIRouter, HTTPException, Depends
from backend.app.models.responses import GraphResponse
from backend.app.services.graph_service import GraphService
from backend.app.api.dependencies import get_graph_service

router = APIRouter()

@router.get("/graph/{standard_id}", response_model=GraphResponse)
def get_graph_data(
    standard_id: str,
    graph_service: GraphService = Depends(get_graph_service)
):
    graph_data = graph_service.get_react_flow_graph(standard_id)
    return GraphResponse(**graph_data)
