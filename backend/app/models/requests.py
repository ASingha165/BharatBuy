from typing import Optional, List
from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=3,
        description="Procurement requirement specification query",
        example="Procurement of electrical cables for 1.1 kV power distribution"
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of top Indian Standards recommendations to return"
    )

class ProcurementRequirementItem(BaseModel):
    item: str = Field(..., min_length=1, description="Product / material name or description")
    quantity: Optional[float] = Field(default=1.0, ge=0, description="Required quantity")
    unit: Optional[str] = Field(default=None, description="Unit of measurement (e.g., meters, units, tonnes)")
    specifications: Optional[str] = Field(default=None, description="Technical specifications or parameters")
    required_certifications: Optional[list[str]] = Field(default_factory=list, description="Explicit certification constraints")

class ProcurementAnalysisRequest(BaseModel):
    company: str = Field(..., min_length=1, description="Startup / Buyer company name", example="Zenith GreenTech Pvt Ltd")
    description: Optional[str] = Field(
        default=None,
        description="Optional natural-language batch procurement requirement description"
    )
    requirements: list[ProcurementRequirementItem] = Field(
        default_factory=list,
        description="Structured list of procurement line items"
    )
    top_k_per_item: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of standards to retrieve per item"
    )
    buyer_latitude: Optional[float] = Field(default=None, ge=6.0, le=37.5)
    buyer_longitude: Optional[float] = Field(default=None, ge=68.0, le=97.5)
    search_radius_km: Optional[float] = Field(default=100.0, gt=0.0, le=5000.0)
    budget_amount: Optional[float] = Field(default=None, ge=0.0)
    budget_tolerance_pct: float = Field(default=10.0, ge=0.0, le=100.0)

class ManualVerifyRequest(BaseModel):
    reference_id: Optional[str] = None
    action: str = Field(default="CONFIRM_MANUAL_VERIFICATION", description="'CONFIRM_MANUAL_VERIFICATION' or 'INITIATE_WORKFLOW'")
    verified_by: str = Field(..., description="Email or identifier of buyer/engineer performing verification")
    checklist_confirmed: dict[str, bool] = Field(default_factory=dict, description="Confirmations for required checklist items")
    notes: Optional[str] = None
