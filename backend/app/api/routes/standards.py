from fastapi import APIRouter, HTTPException, Depends
from typing import List
from backend.app.models.responses import StandardDetailResponse, RelatedStandardItem
from backend.app.repositories.standards_repository import StandardsRepository
from backend.app.services.graph_service import GraphService
from backend.app.api.dependencies import get_repository, get_graph_service

router = APIRouter()

@router.get("/standards/{standard_id}", response_model=StandardDetailResponse)
def get_standard_details(
    standard_id: str,
    repository: StandardsRepository = Depends(get_repository),
    graph_service: GraphService = Depends(get_graph_service)
):
    std = repository.get_standard_by_id(standard_id)
    if not std:
        raise HTTPException(status_code=404, detail=f"Standard '{standard_id}' not found.")
        
    related = graph_service.get_related_standards(std["standard_id"])
    
    return StandardDetailResponse(
        standard_id=std["standard_id"],
        is_code=std["is_code"],
        title=std["title"],
        department=std["department"],
        scope_summary=std["scope_summary"],
        key_specifications=std["key_specifications"],
        testing_requirements=std["testing_requirements"],
        publication_year=std["publication_year"],
        status=std["status"],
        related_standards=related
    )

@router.get("/standards/{standard_id}/related", response_model=List[RelatedStandardItem])
def get_related_standards(
    standard_id: str,
    graph_service: GraphService = Depends(get_graph_service)
):
    return graph_service.get_related_standards(standard_id)
