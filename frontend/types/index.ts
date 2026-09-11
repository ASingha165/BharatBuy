export interface RelatedStandardItem {
  standard_id: string;
  is_code: string;
  relationship_type: string;
  title: string;
  description?: string;
}

export interface RecommendationResultItem {
  standard_id: string;
  is_code: string;
  title: string;
  department: string;
  scope_summary: string;
  key_specifications: string;
  testing_requirements: string;
  publication_year?: number;
  status: string;
  score: number;
  reason: string;
  related_standards: RelatedStandardItem[];
}

export interface RecommendationResponse {
  query: string;
  model?: string;
  total_found: number;
  results: RecommendationResultItem[];
  explanation?: string;
  gemini_explanation?: string;
}

export interface StandardDetailResponse {
  standard_id: string;
  is_code: string;
  title: string;
  department: string;
  scope_summary: string;
  key_specifications: string;
  testing_requirements: string;
  publication_year?: number;
  status: string;
  related_standards: RelatedStandardItem[];
}

export interface GraphNodeData {
  label: string;
  title: string;
  department: string;
  type: string;
}

export interface ReactFlowNode {
  id: string;
  data: GraphNodeData;
  position: { x: number; y: number };
  type?: string;
}

export interface ReactFlowEdge {
  id: string;
  source: string;
  target: string;
  label: string;
  animated?: boolean;
  style?: Record<string, any>;
}

export interface GraphResponse {
  center_standard_id: string;
  nodes: ReactFlowNode[];
  edges: ReactFlowEdge[];
}

export type DataProvenanceLabel =
  | 'AUTHORITATIVE'
  | 'GOVERNMENT_RECORD'
  | 'BIS_EVIDENCE'
  | 'REGISTRY_EVIDENCE'
  | 'BUYER_VERIFIED'
  | 'SUPPLIER_DECLARATION'
  | 'REGION_ONLY'
  | 'DEMO_DATA';

export interface HealthStatus {
  status: string;
  database: boolean;
  model_type?: string;
  total_standards: number;
  gemini_configured?: boolean;
  is_demo_mode?: boolean;
}

export interface ProcurementRequirementItem {
  item: string;
  quantity?: number;
  unit?: string;
  specifications?: string;
  required_certifications?: string[];
}

export interface ProcurementAnalysisRequest {
  company: string;
  description?: string;
  requirements: ProcurementRequirementItem[];
  top_k_per_item?: number;
  buyer_latitude?: number;
  buyer_longitude?: number;
  search_radius_km?: number;
  budget_amount?: number;
  budget_tolerance_pct?: number;
}

export interface NormalizedRequirementItem {
  item_name: string;
  category: string;
  quantity: number;
  unit?: string;
  specifications: string;
  mandatory_certifications: string[];
  inferred_standard_requirements: string[];
  search_terms: string[];
}

export interface ItemComplianceEvaluation {
  item_id: string;
  item_name: string;
  normalized_profile: NormalizedRequirementItem;
  standards: RecommendationResultItem[];
  primary_standard?: RecommendationResultItem;
  compliance_status: 'COMPLIANT' | 'CONDITIONAL_COMPLIANCE' | 'ACTION_REQUIRED' | string;
  score: number;
  applicable_scheme: string;
  is_mandatory_certification: boolean;
  missing_parameters: string[];
  evidence: string[];
  recommendation: string;
}

export interface LocationModel {
  city: string;
  state: string;
  latitude: number;
  longitude: number;
}

export interface ScoreBreakdown {
  category_match: number;
  standard_match: number;
  compliance_evidence: number;
  location_relevance: number;
  data_confidence: number;
  overall_score: number;
}

export type BisCertificationStatus = 
  | 'CONFIRMED'
  | 'EVIDENCE_AVAILABLE'
  | 'REQUIRES_LIVE_VERIFICATION'
  | 'NOT_APPLICABLE'
  | 'NO_EVIDENCE';

export type ProcurementDecisionStatus =
  | 'READY'
  | 'READY_WITH_VERIFICATION'
  | 'INSUFFICIENT_EVIDENCE'
  | 'NOT_RECOMMENDED';

export type FreshnessState = 'CURRENT' | 'AGING' | 'STALE' | 'UNKNOWN';

export type VerificationMethod = 'AUTOMATED' | 'MANUAL' | 'IMPORTED' | 'REGISTRY';

export interface AuditLogEntry {
  log_id: string;
  source_id: string;
  evidence_id?: string | null;
  action: string;
  previous_status: string;
  new_status: string;
  verification_method: string;
  timestamp: string;
  actor: string;
  notes?: string | null;
}

export interface SourceVerificationResponse {
  source_id: string;
  source_name: string;
  source_type: string;
  status: string;
  verification_method: string;
  provenance_label?: DataProvenanceLabel | string;
  is_demo_mode?: boolean;
  official_verification_url?: string | null;
  reference_id?: string | null;
  standard_code?: string | null;
  validity_state: string;
  checks: string[];
  can_auto_verify: boolean;
  audit_trail: AuditLogEntry[];
  instructions: string;
}

export interface ManualVerifyRequest {
  reference_id?: string | null;
  action?: string;
  verified_by: string;
  checklist_confirmed: Record<string, boolean>;
  notes?: string;
}

export interface EvidenceRecord {
  evidence_id: string;
  evidence_type: 'BIS_STANDARD' | 'BIS_LICENSE' | 'GOVERNMENT_RECORD' | 'SOURCE_REGISTRY' | 'PRODUCT_CAPABILITY' | 'LOCATION' | 'VENDOR_DECLARATION' | string;
  title: string;
  description: string;
  source: string;
  source_url?: string | null;
  reference_id?: string | null;
  retrieved_at?: string | null;
  verified_at?: string | null;
  expires_at?: string | null;
  verification_status: 'CONFIRMED' | 'VERIFIED' | 'PARTIAL' | 'REQUIRES_VERIFICATION' | 'FAILED' | 'EXPIRED' | 'UNVERIFIED' | string;
  verification_method?: VerificationMethod | string;
  confidence?: number;
  freshness_state?: FreshnessState | string;
  provenance?: Record<string, any>;
  supports_claim: string;
  claim?: string;
}

export interface TrustBreakdown {
  identity_evidence: number;
  bis_evidence: number;
  evidence_freshness: number;
  evidence_completeness: number;
  trust_score: number;
  trust_level: 'HIGH' | 'MODERATE' | 'LOW' | string;
}

export interface DecisionSummary {
  decision_status?: ProcurementDecisionStatus | string;
  can_procure_now?: boolean;
  all_standards_covered: boolean;
  compliant_sourcing_available: boolean;
  strong_sourcing_items: string[];
  verification_required_items: string[];
  insufficient_evidence_items: string[];
  critical_claims?: Array<{
    claim: string;
    evidence_type: string;
    status: string;
    sufficient: boolean;
    note?: string;
  }>;
  missing_verifications?: string[];
  recommended_actions?: string[];
  procurement_ready: boolean;
  summary_text: string;
}

export interface PackageEvaluation {
  overall_readiness_score: number;
  readiness_level: 'HIGH' | 'MODERATE' | 'LOW' | string;
  decision_status?: ProcurementDecisionStatus | string;
  total_items: number;
  item_coverage: number;
  standards_coverage: number;
  compliance_coverage: number;
  sourcing_coverage: number;
  verification_coverage: number;
  evidence_coverage?: number;
  sourcing_feasibility: string;
  supplier_overlap_count: number;
  decision_summary?: DecisionSummary;
  unresolved_issues: string[];
  action_items: string[];
}

export interface SourcingRecommendationItem {
  source_id?: string;
  source_name?: string;
  supplier_id?: string;
  supplier_name?: string;
  source_type: 'SOURCING_REGION' | 'SUPPLIER' | 'MANUFACTURER' | 'DISTRIBUTOR' | 'MARKETPLACE' | 'UNKNOWN_SOURCE' | string;
  verification_status: 'VERIFIED' | 'PARTIALLY_VERIFIED' | 'REGION_ONLY' | 'UNVERIFIED' | 'REQUIRES_VENDOR_VERIFICATION' | string;
  bis_certification_status?: BisCertificationStatus | string;
  provenance_label?: DataProvenanceLabel | string;
  is_demo_data?: boolean;
  trust_score?: number;
  trust_level?: 'HIGH' | 'MODERATE' | 'LOW' | string;
  trust_breakdown?: TrustBreakdown;
  evidence_records?: EvidenceRecord[];
  verification_evidence?: string[];
  compliance_evidence?: string[];
  location: LocationModel | string;
  state?: string;
  latitude?: number;
  longitude?: number;
  supported_items: string[];
  relevant_standards: string[];
  bis_relevance?: string[];
  suitability_score: number;
  confidence: number;
  explanation?: string;
  reasoning?: string[];
  score_breakdown?: ScoreBreakdown;
  vendor_identity?: VendorIdentity;
  official_record_status?: string;
  official_record_source?: string;
  distance_from_buyer_km?: number | null;
  range_status?: string;
  cost_assessment?: CostAssessment;
}

export interface GSTINVerification {
  gstin?: string | null;
  status: string;
  verification_source: string;
  verified_at?: string | null;
  confidence: number;
  message: string;
}

export interface VendorIdentity {
  vendor_id?: string | null;
  legal_name?: string | null;
  trade_name?: string | null;
  gstin_verification: GSTINVerification;
  registration_status: string;
  registered_address?: string | null;
  provenance: string;
}

export interface CostAssessment {
  estimated_unit_cost?: number | null;
  estimated_total_cost?: number | null;
  status: string;
  currency: string;
  note: string;
}

export interface SourceEvidenceResponse {
  source_id: string;
  source_name: string;
  source_type: string;
  verification_status: string;
  bis_certification_status: string;
  provenance_label?: DataProvenanceLabel | string;
  is_demo_data?: boolean;
  trust_score: number;
  trust_level: string;
  evidence: EvidenceRecord[];
  provenance_chain?: Array<Record<string, any>>;
  freshness_summary?: Record<string, any>;
}

export interface MapPointItem {
  id: string;
  title: string;
  location: string;
  latitude: number;
  longitude: number;
  source_type: string;
  verification_status?: string;
  provenance_label?: DataProvenanceLabel | string;
  is_demo_data?: boolean;
  categories: string[];
  supported_items: string[];
  relevant_standards?: string[];
  suitability_score: number;
  evidence_preview?: string[];
  distance_from_buyer_km?: number | null;
  range_status?: string;
  official_record_status?: string;
}

export interface GroundedExplanation {
  summary: string;
  supported_by_data: string[];
  inference_requires_verification: string[];
  compliance_caveats: string[];
  missing_information: string[];
  synthesis_type?: 'LIVE_GEMINI_SYNTHESIS' | 'GROUNDED_DETERMINISTIC_FALLBACK' | string;
}

export interface ProcurementAnalysisResponse {
  request_id: string;
  company: string;
  model: string;
  is_demo_mode?: boolean;
  items: ItemComplianceEvaluation[];
  package_evaluation: PackageEvaluation;
  recommendations: SourcingRecommendationItem[];
  official_records?: SourcingRecommendationItem[];
  map_points: MapPointItem[];
  explanation: GroundedExplanation;
  search_expansion?: {
    requested_radius_km?: number | null;
    applied_radius_km?: number | null;
    expanded: boolean;
    expansion_steps: number[];
    message: string;
  };
  package_sourcing?: {
    strategy: string;
    explanation: string;
  };
  buyer_location?: LocationModel | null;
  budget_status?: string;
  package_total_cost?: number | null;
}

// Authentication Types
export interface AuthUser {
  id: string;
  name: string;
  email: string;
  organization: string;
  created_at: string;
}

export interface AuthResponse {
  user: AuthUser;
  token: string;
  message: string;
}

export interface SignUpPayload {
  name: string;
  email: string;
  organization: string;
  password: string;
  confirm_password: string;
  terms_accepted: boolean;
}

export interface SignInPayload {
  email: string;
  password: string;
  remember_me?: boolean;
}
