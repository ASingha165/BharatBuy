from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from backend.app.models.requests import ProcurementAnalysisRequest, ManualVerifyRequest
from backend.app.models.responses import (
    ProcurementAnalysisResponse,
    SourceEvidenceResponse,
    SourceVerificationResponse
)
from backend.app.models.auth import UserResponse
from backend.app.api.routes.auth import get_current_user_optional
from backend.app.services.procurement_service import ProcurementService
from backend.app.services.sourcing_service import SourcingService
from backend.app.api.dependencies import get_procurement_service, get_sourcing_service
from backend.app.core.logging import logger

router = APIRouter()

@router.post("/analyze", response_model=ProcurementAnalysisResponse)
def analyze_procurement(
    payload: ProcurementAnalysisRequest,
    service: ProcurementService = Depends(get_procurement_service),
    current_user: Optional[UserResponse] = Depends(get_current_user_optional)
):
    logger.info(f"[API ROUTE] Procurement analysis requested for company '{payload.company}' ({len(payload.requirements)} items)")
    if not payload.company or not payload.company.strip():
        raise HTTPException(status_code=400, detail="Company name cannot be empty.")

    if not payload.requirements and (not payload.description or not payload.description.strip()):
        raise HTTPException(
            status_code=400,
            detail="Either 'requirements' list or a natural-language 'description' must be provided."
        )

    try:
        response = service.analyze(payload)
        logger.info(f"[API ROUTE] Analysis complete for request '{response.request_id}' (Readiness: {response.package_evaluation.overall_readiness_score}%)")

        # If user is authenticated, securely persist request in Cloud Firestore using verified UID
        if current_user and current_user.id:
            try:
                from backend.app.services.firestore_service import firestore_service
                firestore_service.record_procurement_request(
                    verified_firebase_uid=current_user.id,
                    request_id=response.request_id,
                    organization_name=payload.company,
                    requirements=[r.dict() for r in payload.requirements] if payload.requirements else payload.description,
                    normalized_metadata={
                        "total_items": len(response.normalized_items),
                        "overall_readiness_score": response.package_evaluation.overall_readiness_score,
                        "decision_state": response.package_evaluation.decision_summary.decision_state
                    },
                    status="COMPLETED",
                    items=[
                        {
                            "item_id": it.item_id,
                            "product_type": it.product_type,
                            "specifications": it.specifications,
                            "matched_standards": [s.is_code for s in it.matched_standards],
                            "compliance_status": it.compliance_status
                        }
                        for it in response.normalized_items
                    ]
                )
            except Exception as e:
                logger.debug(f"[API ROUTE] Firestore recording note: {e}")

        return response
    except Exception as e:
        logger.error(f"[API ROUTE] Error during procurement analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal procurement analysis error: {str(e)}")

@router.get("/sources", response_model=List[Dict[str, Any]])
def list_sources(
    category: Optional[str] = Query(None, description="Filter sources by product category (e.g. cable, steel, solar)"),
    standard_id: Optional[str] = Query(None, description="Filter sources by supported Indian Standard (e.g. IS-1786)"),
    verification_status: Optional[str] = Query(None, description="Filter by verification status (VERIFIED, PARTIALLY_VERIFIED, REGION_ONLY, etc.)"),
    source_type: Optional[str] = Query(None, description="Filter by source type (SOURCING_REGION, MANUFACTURER, DISTRIBUTOR, etc.)"),
    sourcing_svc: SourcingService = Depends(get_sourcing_service)
):
    """
    Returns registered source records and industrial corridors in BharatBuy Sourcing Intelligence.
    Guarantees zero-fabrication of unverified corporate entities.
    """
    logger.info(f"[API ROUTE] Listing sources: category={category}, standard={standard_id}, status={verification_status}, type={source_type}")
    sources = sourcing_svc.get_all_sources(
        category=category,
        standard_id=standard_id,
        verification_status=verification_status,
        source_type=source_type
    )
    return sources

@router.get("/sources/{source_id}", response_model=Dict[str, Any])
def get_source_details(
    source_id: str,
    sourcing_svc: SourcingService = Depends(get_sourcing_service)
):
    """
    Retrieves full verified metadata, location coordinates, standards conformance, and BIS license evidence for a source.
    """
    logger.info(f"[API ROUTE] Sourcing details requested for source '{source_id}'")
    source = sourcing_svc.get_source_by_id(source_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"Sourcing entity '{source_id}' not found in registry.")
    return source

@router.get("/sources/{source_id}/evidence", response_model=SourceEvidenceResponse)
def get_source_evidence(
    source_id: str,
    sourcing_svc: SourcingService = Depends(get_sourcing_service)
):
    """
    Retrieves explicit, auditable Claim -> Evidence records, BIS license verification status,
    and trust score breakdown for a specific sourcing entity.
    """
    logger.info(f"[API ROUTE] Sourcing evidence requested for source '{source_id}'")
    evidence_data = sourcing_svc.get_source_evidence(source_id)
    if not evidence_data:
        raise HTTPException(status_code=404, detail=f"Sourcing entity '{source_id}' not found in registry.")
    return evidence_data

@router.get("/sources/{source_id}/verification", response_model=SourceVerificationResponse)
def get_source_verification(
    source_id: str,
    sourcing_svc: SourcingService = Depends(get_sourcing_service)
):
    """
    Retrieves official BIS verification workflow, reference details, and buyer audit trail for a source.
    """
    logger.info(f"[API ROUTE] Verification workflow requested for source '{source_id}'")
    verif = sourcing_svc.get_source_verification(source_id)
    if not verif:
        raise HTTPException(status_code=404, detail=f"Sourcing entity '{source_id}' not found in registry.")
    return verif

@router.post("/sources/{source_id}/verify", response_model=SourceVerificationResponse)
def verify_source(
    source_id: str,
    payload: ManualVerifyRequest,
    sourcing_svc: SourcingService = Depends(get_sourcing_service)
):
    """
    Records an explicit buyer manual verification.
    Does NOT fabricate external automated verification when access controls exist.
    Stores an immutable audit trail entry with verified_by, verified_at, and method = MANUAL.
    """
    logger.info(f"[API ROUTE] Manual verification submitted for source '{source_id}' by '{payload.verified_by}'")
    verif = sourcing_svc.verify_source_manually(source_id, payload)
    if not verif:
        raise HTTPException(status_code=404, detail=f"Sourcing entity '{source_id}' not found in registry.")
    return verif

