from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

class RelatedStandardItem(BaseModel):
    standard_id: str
    is_code: str
    relationship_type: str
    title: str
    description: Optional[str] = None

class RecommendationResultItem(BaseModel):
    standard_id: str
    is_code: str
    title: str
    department: str
    scope_summary: str
    key_specifications: str
    testing_requirements: str
    publication_year: Optional[int] = None
    status: str
    score: float = Field(..., description="Recommendation relevance confidence score (0 to 1)")
    reason: str = Field(..., description="Technical justification for recommendation")
    related_standards: List[RelatedStandardItem] = []

class RecommendationResponse(BaseModel):
    query: str
    model: str = Field(default="baseline", description="Active recommendation model engine ('baseline' or 'custom')")
    total_found: int
    results: List[RecommendationResultItem]
    explanation: Optional[str] = Field(
        default=None,
        description="Grounded technical explanation detailing why these standards match"
    )

class StandardDetailResponse(BaseModel):
    standard_id: str
    is_code: str
    title: str
    department: str
    scope_summary: str
    key_specifications: str
    testing_requirements: str
    publication_year: Optional[int] = None
    status: str
    related_standards: List[RelatedStandardItem] = []

class GraphNodeData(BaseModel):
    label: str
    title: str
    department: str
    type: str = "DEFAULT"

class ReactFlowNode(BaseModel):
    id: str
    data: GraphNodeData
    position: Dict[str, float]
    type: str = "default"

class ReactFlowEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str
    animated: bool = False
    style: Optional[Dict[str, Any]] = None

class GraphResponse(BaseModel):
    center_standard_id: str
    nodes: List[ReactFlowNode]
    edges: List[ReactFlowEdge]

class HealthStatusResponse(BaseModel):
    status: str
    database: bool
    model_type: str
    total_standards: int
    gemini_configured: bool
    is_demo_mode: bool = False

class NormalizedRequirementItem(BaseModel):
    item_name: str
    category: str
    quantity: float = 1.0
    unit: Optional[str] = None
    specifications: str = ""
    mandatory_certifications: List[str] = []
    inferred_standard_requirements: List[str] = []
    search_terms: List[str] = []

class ItemComplianceEvaluation(BaseModel):
    item_id: str
    item_name: str
    normalized_profile: NormalizedRequirementItem
    standards: List[RecommendationResultItem] = []
    primary_standard: Optional[RecommendationResultItem] = None
    compliance_status: str = Field(..., description="'COMPLIANT', 'CONDITIONAL_COMPLIANCE', or 'ACTION_REQUIRED'")
    score: float = Field(..., ge=0.0, le=1.0, description="Compliance & relevance confidence score")
    applicable_scheme: str = Field(default="Voluntary", description="BIS scheme: 'ISI Mark (Scheme I)', 'CRS', etc.")
    is_mandatory_certification: bool = False
    missing_parameters: List[str] = []
    evidence: List[str] = []
    recommendation: str = ""

from enum import Enum

class EvidenceType(str, Enum):
    BIS_STANDARD = "BIS_STANDARD"
    BIS_LICENSE = "BIS_LICENSE"
    GOVERNMENT_RECORD = "GOVERNMENT_RECORD"
    SOURCE_REGISTRY = "SOURCE_REGISTRY"
    PRODUCT_CAPABILITY = "PRODUCT_CAPABILITY"
    LOCATION = "LOCATION"
    VENDOR_DECLARATION = "VENDOR_DECLARATION"

class VerificationStatusEnum(str, Enum):
    VERIFIED = "VERIFIED"
    CONFIRMED = "CONFIRMED"
    PARTIAL = "PARTIAL"
    REQUIRES_VERIFICATION = "REQUIRES_VERIFICATION"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    UNVERIFIED = "UNVERIFIED"

ExtendedVerificationStatus = VerificationStatusEnum

class FreshnessState(str, Enum):
    CURRENT = "CURRENT"
    AGING = "AGING"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"

class VerificationMethod(str, Enum):
    AUTOMATED = "AUTOMATED"
    MANUAL = "MANUAL"
    IMPORTED = "IMPORTED"
    REGISTRY = "REGISTRY"

class BisCertificationStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    EVIDENCE_AVAILABLE = "EVIDENCE_AVAILABLE"
    REQUIRES_LIVE_VERIFICATION = "REQUIRES_LIVE_VERIFICATION"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NO_EVIDENCE = "NO_EVIDENCE"

class ProcurementDecisionStatus(str, Enum):
    READY = "READY"
    READY_WITH_VERIFICATION = "READY_WITH_VERIFICATION"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    NOT_RECOMMENDED = "NOT_RECOMMENDED"

DecisionStatus = ProcurementDecisionStatus

class DataProvenanceLabel(str, Enum):
    AUTHORITATIVE = "AUTHORITATIVE"
    GOVERNMENT_RECORD = "GOVERNMENT_RECORD"
    BIS_EVIDENCE = "BIS_EVIDENCE"
    REGISTRY_EVIDENCE = "REGISTRY_EVIDENCE"
    BUYER_VERIFIED = "BUYER_VERIFIED"
    SUPPLIER_DECLARATION = "SUPPLIER_DECLARATION"
    REGION_ONLY = "REGION_ONLY"
    DEMO_DATA = "DEMO_DATA"

class EvidenceRecord(BaseModel):
    evidence_id: str
    evidence_type: str = Field(..., description="BIS_STANDARD | BIS_LICENSE | GOVERNMENT_RECORD | SOURCE_REGISTRY | PRODUCT_CAPABILITY | LOCATION | VENDOR_DECLARATION")
    title: str
    description: str
    source: str
    source_url: Optional[str] = None
    reference_id: Optional[str] = None
    retrieved_at: Optional[str] = None
    verified_at: Optional[str] = None
    expires_at: Optional[str] = None
    verification_status: str = Field(..., description="CONFIRMED | VERIFIED | PARTIAL | REQUIRES_VERIFICATION | FAILED | EXPIRED | UNVERIFIED")
    verification_method: str = Field(default="REGISTRY", description="AUTOMATED | MANUAL | IMPORTED | REGISTRY")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    freshness_state: str = Field(default="UNKNOWN", description="CURRENT | AGING | STALE | UNKNOWN")
    provenance: Optional[Dict[str, Any]] = None
    supports_claim: str = ""
    claim: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        if not self.supports_claim and self.claim:
            self.supports_claim = self.claim
        elif not self.claim and self.supports_claim:
            self.claim = self.supports_claim

class TrustBreakdown(BaseModel):
    identity_evidence: float = Field(..., ge=0.0, le=1.0)
    bis_evidence: float = Field(..., ge=0.0, le=1.0)
    evidence_freshness: float = Field(..., ge=0.0, le=1.0)
    evidence_completeness: float = Field(..., ge=0.0, le=1.0)
    trust_score: float = Field(..., ge=0.0, le=1.0)
    trust_level: str = Field(..., description="'HIGH', 'MODERATE', or 'LOW'")

class LocationModel(BaseModel):
    city: str
    state: str
    latitude: float
    longitude: float

class GSTINVerification(BaseModel):
    gstin: Optional[str] = None
    status: str = "UNVERIFIED"
    verification_source: str = "NOT_CONFIGURED"
    verified_at: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    message: str = "GSTIN verification is unavailable; no authoritative provider is configured."

class VendorIdentity(BaseModel):
    vendor_id: Optional[str] = None
    legal_name: Optional[str] = None
    trade_name: Optional[str] = None
    gstin_verification: GSTINVerification = Field(default_factory=GSTINVerification)
    registration_status: str = "UNKNOWN"
    registered_address: Optional[str] = None
    provenance: str = "REGISTRY_ONLY"

class CostAssessment(BaseModel):
    estimated_unit_cost: Optional[float] = None
    estimated_total_cost: Optional[float] = None
    status: str = "COST_UNKNOWN"
    currency: str = "INR"
    note: str = "PRICE NOT AVAILABLE; no supplier price was provided."

class SearchExpansion(BaseModel):
    requested_radius_km: Optional[float] = None
    applied_radius_km: Optional[float] = None
    expanded: bool = False
    expansion_steps: List[float] = []
    message: str = ""

class PackageSourcing(BaseModel):
    strategy: str = "ITEM_BY_ITEM_SOURCING"
    explanation: str = "Item-level sourcing is used because supplier capability is evaluated per procurement item."

class ScoreBreakdown(BaseModel):
    category_match: float = Field(..., ge=0.0, le=1.0)
    standard_match: float = Field(..., ge=0.0, le=1.0)
    compliance_evidence: float = Field(..., ge=0.0, le=1.0)
    location_relevance: float = Field(..., ge=0.0, le=1.0)
    data_confidence: float = Field(..., ge=0.0, le=1.0)
    overall_score: float = Field(..., ge=0.0, le=100.0)

class DecisionSummary(BaseModel):
    decision_status: str = Field(default="READY_WITH_VERIFICATION", description="'READY', 'READY_WITH_VERIFICATION', 'INSUFFICIENT_EVIDENCE', or 'NOT_RECOMMENDED'")
    can_procure_now: bool = True
    all_standards_covered: bool
    compliant_sourcing_available: bool
    strong_sourcing_items: List[str] = []
    verification_required_items: List[str] = []
    insufficient_evidence_items: List[str] = []
    critical_claims: List[Dict[str, Any]] = []
    missing_verifications: List[str] = []
    recommended_actions: List[str] = []
    procurement_ready: bool
    summary_text: str

class PackageEvaluation(BaseModel):
    overall_readiness_score: float = Field(..., ge=0.0, le=100.0, description="Readiness percentage index (0-100)")
    readiness_level: str = Field(..., description="'HIGH', 'MODERATE', or 'LOW'")
    decision_status: str = Field(default="READY_WITH_VERIFICATION", description="'READY', 'READY_WITH_VERIFICATION', 'INSUFFICIENT_EVIDENCE', or 'NOT_RECOMMENDED'")
    total_items: int
    item_coverage: float = Field(..., description="Proportion of items with high-confidence standards")
    standards_coverage: float = Field(..., description="Proportion of items with at least one matching standard")
    compliance_coverage: float = Field(..., description="Proportion of items meeting compliance baseline")
    sourcing_coverage: float = Field(default=0.0, description="Proportion of items with eligible sourcing options")
    verification_coverage: float = Field(default=0.0, description="Proportion of items with documented/eligible manufacturer records")
    evidence_coverage: float = Field(default=0.0, description="Proportion of items with documented source evidence attached")
    sourcing_feasibility: str
    supplier_overlap_count: int = 0
    decision_summary: Optional[DecisionSummary] = None
    unresolved_issues: List[str] = []
    action_items: List[str] = []

class SourcingRecommendationItem(BaseModel):
    source_id: str
    source_name: str
    source_type: str = Field(..., description="'SOURCING_REGION', 'SUPPLIER', 'MANUFACTURER', 'DISTRIBUTOR', 'MARKETPLACE', or 'UNKNOWN_SOURCE'")
    verification_status: str = Field(..., description="'VERIFIED', 'PARTIALLY_VERIFIED', 'REGION_ONLY', 'UNVERIFIED', or 'REQUIRES_VENDOR_VERIFICATION'")
    bis_certification_status: str = Field(default="REQUIRES_LIVE_VERIFICATION", description="'CONFIRMED', 'EVIDENCE_AVAILABLE', 'REQUIRES_LIVE_VERIFICATION', 'NOT_APPLICABLE', or 'NO_EVIDENCE'")
    provenance_label: str = Field(default="REGISTRY_EVIDENCE", description="'AUTHORITATIVE', 'GOVERNMENT_RECORD', 'BIS_EVIDENCE', 'REGISTRY_EVIDENCE', 'BUYER_VERIFIED', 'SUPPLIER_DECLARATION', 'REGION_ONLY', or 'DEMO_DATA'")
    is_demo_data: bool = Field(default=False, description="Flag indicating if record is simulated demo data")
    trust_score: float = Field(default=0.5, ge=0.0, le=1.0)
    trust_level: str = Field(default="MODERATE", description="'HIGH', 'MODERATE', or 'LOW'")
    trust_breakdown: Optional[TrustBreakdown] = None
    evidence_records: List[EvidenceRecord] = []
    verification_evidence: List[str] = []
    location: LocationModel
    supported_items: List[str] = []
    relevant_standards: List[str] = []
    bis_relevance: List[str] = []
    suitability_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: List[str] = []
    score_breakdown: Optional[ScoreBreakdown] = None

    # Backward-compatibility aliases for existing code and tests:
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    compliance_evidence: List[str] = []
    explanation: Optional[str] = None
    vendor_identity: VendorIdentity = Field(default_factory=VendorIdentity)
    official_record_status: str = "UNVERIFIED"
    official_record_source: str = "BharatBuy registry; authoritative vendor verification unavailable"
    distance_from_buyer_km: Optional[float] = None
    range_status: str = "DISTANCE_UNKNOWN"
    cost_assessment: CostAssessment = Field(default_factory=CostAssessment)

    def model_post_init(self, __context: Any) -> None:
        # Populate backward-compatible fields automatically if not set
        if self.supplier_id is None:
            self.supplier_id = self.source_id
        if self.supplier_name is None:
            self.supplier_name = self.source_name
        if self.state is None:
            self.state = self.location.state
        if self.latitude is None:
            self.latitude = self.location.latitude
        if self.longitude is None:
            self.longitude = self.location.longitude
        if not self.compliance_evidence:
            self.compliance_evidence = list(self.verification_evidence)
        if self.explanation is None:
            self.explanation = " ".join(self.reasoning) if self.reasoning else f"{self.source_name} matched for {', '.join(self.supported_items)}."

class AuditLogEntry(BaseModel):
    log_id: str
    source_id: str
    evidence_id: Optional[str] = None
    action: str
    previous_status: str
    new_status: str
    verification_method: str = "MANUAL"
    timestamp: str
    actor: str
    notes: Optional[str] = None

class VerificationWorkflowCheck(BaseModel):
    check_id: str
    label: str
    confirmed: bool = False

class SourceVerificationResponse(BaseModel):
    source_id: str
    source_name: str
    source_type: str
    status: str
    verification_method: str = "REGISTRY"
    provenance_label: str = "REGISTRY_EVIDENCE"
    is_demo_mode: bool = False
    official_verification_url: Optional[str] = None
    reference_id: Optional[str] = None
    standard_code: Optional[str] = None
    validity_state: str = "UNKNOWN"
    checks: List[str] = []
    can_auto_verify: bool = False
    audit_trail: List[AuditLogEntry] = []
    instructions: str = ""

class SourceEvidenceResponse(BaseModel):
    source_id: str
    source_name: str
    source_type: str
    verification_status: str
    bis_certification_status: str
    provenance_label: str = "REGISTRY_EVIDENCE"
    is_demo_data: bool = False
    trust_score: float
    trust_level: str
    evidence: List[EvidenceRecord]
    provenance_chain: Optional[List[Dict[str, Any]]] = None
    freshness_summary: Optional[Dict[str, Any]] = None

class MapPointItem(BaseModel):
    id: str
    title: str
    location: str
    latitude: float
    longitude: float
    source_type: str
    verification_status: str = "REGION_ONLY"
    provenance_label: str = "REGISTRY_EVIDENCE"
    is_demo_data: bool = False
    categories: List[str] = []
    supported_items: List[str] = []
    relevant_standards: List[str] = []
    suitability_score: float = 0.0
    evidence_preview: List[str] = []
    distance_from_buyer_km: Optional[float] = None
    range_status: str = "DISTANCE_UNKNOWN"
    official_record_status: str = "UNVERIFIED"

class GroundedExplanation(BaseModel):
    summary: str
    supported_by_data: List[str] = []
    inference_requires_verification: List[str] = []
    compliance_caveats: List[str] = []
    missing_information: List[str] = []
    synthesis_type: str = "GROUNDED_DETERMINISTIC_FALLBACK"

class ProcurementAnalysisResponse(BaseModel):
    request_id: str
    company: str
    model: str = "hybrid-baseline"
    is_demo_mode: bool = False
    items: List[ItemComplianceEvaluation]
    package_evaluation: PackageEvaluation
    recommendations: List[SourcingRecommendationItem]
    official_records: List[SourcingRecommendationItem] = []
    map_points: List[MapPointItem]
    explanation: GroundedExplanation
    search_expansion: SearchExpansion = Field(default_factory=SearchExpansion)
    package_sourcing: PackageSourcing = Field(default_factory=PackageSourcing)
    buyer_location: Optional[LocationModel] = None
    budget_status: str = "COST_UNKNOWN"
    package_total_cost: Optional[float] = None


