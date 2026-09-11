import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.responses import (
    EvidenceRecord,
    EvidenceType,
    VerificationStatusEnum,
    FreshnessState,
    VerificationMethod,
    AuditLogEntry,
    ProcurementDecisionStatus,
    BisCertificationStatus,
    NormalizedRequirementItem,
    RecommendationResultItem,
    ItemComplianceEvaluation,
    SourcingRecommendationItem,
    ScoreBreakdown,
    LocationModel
)
from backend.app.models.requests import ManualVerifyRequest
from backend.app.services.audit_service import AuditService
from backend.app.services.providers.provider_registry import get_provider_registry
from backend.app.services.providers.bis_provider import BisEvidenceProvider
from backend.app.services.providers.government_provider import GovernmentRecordProvider
from backend.app.services.providers.supplier_provider import SupplierEvidenceProvider
from backend.app.services.evidence_service import EvidenceService
from backend.app.services.sourcing_service import SourcingService
from backend.app.services.package_evaluation_service import PackageEvaluationService
from backend.app.services.explanation_service import ExplanationService

client = TestClient(app)


# 1. EvidenceProvider Abstraction & Registry
def test_provider_registry_and_providers():
    registry = get_provider_registry()
    
    # Check BIS provider
    bis_provider = registry.get_provider_for_evidence_type(EvidenceType.BIS_LICENSE.value)
    assert isinstance(bis_provider, BisEvidenceProvider)
    assert "Bureau of Indian Standards" in bis_provider.provider_name
    assert bis_provider.can_auto_verify is False
    
    # Check Government Record provider
    gov_provider = registry.get_provider_for_evidence_type(EvidenceType.GOVERNMENT_RECORD.value)
    assert isinstance(gov_provider, GovernmentRecordProvider)
    assert "Government" in gov_provider.provider_name
    assert gov_provider.can_auto_verify is True
    
    # Check Supplier provider
    sup_provider = registry.get_provider_for_evidence_type(EvidenceType.VENDOR_DECLARATION.value)
    assert isinstance(sup_provider, SupplierEvidenceProvider)
    assert "Supplier" in sup_provider.provider_name
    assert sup_provider.can_auto_verify is False


# 2. BIS Provider URL formatting and guided verification
def test_bis_provider_guided_verification():
    bis_provider = BisEvidenceProvider()
    
    # Validate workflow instructions and checklist
    workflow = bis_provider.get_buyer_verification_workflow(
        reference_id="CM/L-0003042",
        standard_code="IS-1786",
        product_category="steel",
        source_name="SAIL Bokaro Steel Plant"
    )
    assert "manakonline.in" in workflow["official_verification_url"]
    assert len(workflow["checks"]) >= 5
    assert workflow["can_auto_verify"] is False
    
    # Provenance generation
    prov = bis_provider.provenance({"reference_id": "CM/L-0003042"})
    assert prov["statutory_authority"] == "Bureau of Indian Standards Act, 2016"
    assert "manakonline.in" in prov["official_url"]
    assert prov["verification_mode"] == "MANUAL_GUIDED_WORKFLOW"


# 3. Freshness State Logic (CURRENT, STALE, UNKNOWN)
def test_freshness_state_calculation():
    evidence_svc = EvidenceService()
    now = datetime.now(timezone.utc)
    
    # 1. Unknown: No retrieval date
    assert evidence_svc.calculate_freshness(None, 90) == FreshnessState.UNKNOWN.value
    assert evidence_svc.calculate_freshness("", 90) == FreshnessState.UNKNOWN.value
    
    # 2. Current: Retrieved 10 days ago (within 90-day TTL)
    retrieved_recent = (now - timedelta(days=10)).isoformat()
    assert evidence_svc.calculate_freshness(retrieved_recent, 90) == FreshnessState.CURRENT.value
    
    # 3. Stale: Retrieved 120 days ago (exceeds 90-day TTL)
    retrieved_old = (now - timedelta(days=120)).isoformat()
    assert evidence_svc.calculate_freshness(retrieved_old, 90) == FreshnessState.STALE.value


# 4. Audit Trail Service Recording and Retrieval
def test_audit_service():
    audit_svc = AuditService()
    initial_count = len(audit_svc.get_logs_for_source("SRC-TEST-AUDIT"))
    
    entry = audit_svc.record(
        source_id="SRC-TEST-AUDIT",
        evidence_id="EV-TEST-001",
        action="MANUAL_BUYER_VERIFICATION",
        previous_status="REQUIRES_LIVE_VERIFICATION",
        new_status="VERIFIED",
        verification_method="MANUAL",
        actor="lead_procurement_officer@zenith.in",
        notes="Verified active CML status on manakonline.in"
    )
    
    assert isinstance(entry, AuditLogEntry)
    assert entry.source_id == "SRC-TEST-AUDIT"
    assert entry.actor == "lead_procurement_officer@zenith.in"
    
    logs = audit_svc.get_logs_for_source("SRC-TEST-AUDIT")
    assert len(logs) == initial_count + 1
    assert logs[-1].action == "MANUAL_BUYER_VERIFICATION"
    assert logs[-1].new_status == "VERIFIED"


# 5. REST Endpoints: GET verification and POST verify
def test_verification_api_endpoints():
    # 1. Query existing authentic source: SRC-MFR-SAIL-BOKARO
    resp = client.get("/api/v1/procurement/sources/SRC-MFR-SAIL-BOKARO/verification")
    assert resp.status_code == 200
    data = resp.json()
    assert data["source_id"] == "SRC-MFR-SAIL-BOKARO"
    assert "checks" in data
    assert len(data["checks"]) >= 4
    assert "official_verification_url" in data
    assert "manakonline.in" in data["official_verification_url"]
    assert "audit_trail" in data
    
    # 2. Submit manual buyer verification
    verify_payload = {
        "verified_by": "qa_auditor@startup.org",
        "reference_id": "CM/L-0003042",
        "notes": "Verified active license on BIS Manakonline portal",
        "confirmations": [
            "Active status confirmed on official portal",
            "Manufacturer identity matches procurement requirement",
            "Scope covers required Grade Fe 500D"
        ]
    }
    post_resp = client.post("/api/v1/procurement/sources/SRC-MFR-SAIL-BOKARO/verify", json=verify_payload)
    assert post_resp.status_code == 200
    post_data = post_resp.json()
    assert post_data["source_id"] == "SRC-MFR-SAIL-BOKARO"
    assert post_data["status"] == "CONFIRMED"
    assert post_data["verification_method"] == "MANUAL"
    assert any(log["actor"] == "qa_auditor@startup.org" for log in post_data["audit_trail"])
    
    # 3. Verify that GET reflects the manual verification
    resp2 = client.get("/api/v1/procurement/sources/SRC-MFR-SAIL-BOKARO/verification")
    data2 = resp2.json()
    assert data2["status"] == "CONFIRMED"
    assert any(log["actor"] == "qa_auditor@startup.org" for log in data2["audit_trail"])


# 6. Decoupled Scoring: Manual verification upgrades Trust without altering Product Suitability
def test_decoupled_scoring_preserves_suitability():
    sourcing_svc = SourcingService()
    
    # Authentic source with CML
    source = sourcing_svc.get_source_by_id("SRC-MFR-SAIL-BOKARO")
    assert source is not None
    
    # Suitability score before
    suit_bd_before = sourcing_svc.calculate_score(
        source=source,
        item_category="steel",
        item_specs="Fe 500D TMT rebars per IS 1786",
        matching_standard_ids=["IS-1786"]
    )
    
    # Trust score before manual verification
    trust_before, _ = sourcing_svc.evidence_service.evaluate_source_trust(source)
    
    # Buyer performs manual verification on portal
    sourcing_svc.verify_source_manually(
        source_id="SRC-MFR-SAIL-BOKARO",
        request=ManualVerifyRequest(
            verified_by="procurement_officer@zenith.in",
            reference_id="CM/L-0003042",
            notes="Confirmed active status on manakonline portal"
        )
    )
    
    # Trust score after manual verification
    trust_after, _ = sourcing_svc.evidence_service.evaluate_source_trust(source)
    
    # Suitability score after manual verification
    suit_bd_after = sourcing_svc.calculate_score(
        source=source,
        item_category="steel",
        item_specs="Fe 500D TMT rebars per IS 1786",
        matching_standard_ids=["IS-1786"]
    )
    
    # Invariant: Suitability remains identical, trust is elevated
    assert suit_bd_before.overall_score == suit_bd_after.overall_score
    assert suit_bd_before.category_match == suit_bd_after.category_match
    assert suit_bd_before.standard_match == suit_bd_after.standard_match
    assert trust_after.trust_score >= trust_before.trust_score


# 7. 4-State Procurement Decisions: Absence of "Immediate PO release"
def test_procurement_decision_semantics():
    pkg_svc = PackageEvaluationService()
    norm = NormalizedRequirementItem(
        item_name="Fe 500 TMT Steel Rebars",
        category="Steel",
        quantity=100.0,
        unit="tonnes",
        specifications="High strength Fe 500 deformed bars per IS 1786",
        search_terms=["steel", "rebar"]
    )
    std = RecommendationResultItem(
        standard_id="IS-1786",
        is_code="IS 1786",
        title="High Strength Deformed Steel Bars",
        department="Civil",
        scope_summary="Structural steel",
        key_specifications="Fe 500",
        testing_requirements="Tensile test",
        status="ACTIVE",
        score=0.95,
        reason="Direct match"
    )
    item_eval = ItemComplianceEvaluation(
        item_id="ITEM-01",
        item_name=norm.item_name,
        normalized_profile=norm,
        standards=[std],
        primary_standard=std,
        compliance_status="COMPLIANT",
        score=0.95,
        applicable_scheme="ISI Mark (Scheme I)",
        is_mandatory_certification=True,
        missing_parameters=[],
        evidence=["Governed by IS 1786"],
        recommendation="Ready for procurement"
    )
    verified_rec = SourcingRecommendationItem(
        source_id="SRC-MFR-SAIL-BOKARO",
        source_name="SAIL Bokaro Steel Plant",
        source_type="MANUFACTURER",
        verification_status="VERIFIED",
        bis_certification_status="REQUIRES_LIVE_VERIFICATION",
        trust_score=0.88,
        trust_level="HIGH",
        location=LocationModel(city="Bokaro", state="Jharkhand", latitude=23.66, longitude=86.15),
        supported_items=[norm.item_name],
        relevant_standards=["IS-1786"],
        suitability_score=0.92,
        confidence=0.88,
        reasoning=["Verified manufacturer."],
        score_breakdown=ScoreBreakdown(
            category_match=1.0, standard_match=1.0, compliance_evidence=1.0,
            location_relevance=1.0, data_confidence=1.0, overall_score=95.0
        )
    )
    
    pkg_eval = pkg_svc.evaluate_package([item_eval], sourcing_recs=[verified_rec])
    
    # Invariant: Never allow autonomous PO release
    assert "Immediate PO release" not in pkg_eval.decision_summary.summary_text
    assert "autonomous" not in pkg_eval.decision_summary.summary_text.lower()
    assert (
        "buyer approval" in pkg_eval.decision_summary.summary_text.lower()
        or "procurement-ready" in pkg_eval.decision_summary.summary_text.lower()
        or "verification" in pkg_eval.decision_summary.summary_text.lower()
    )


# 8. Grounded AI Explanation Guardrails: No fabricated verifications or PO releases
def test_grounded_explanation_guardrails():
    exp_svc = ExplanationService(gemini_api_key=None)
    
    norm = NormalizedRequirementItem(
        item_name="1.1 kV XLPE Power Cable",
        category="Cable",
        specifications="Working voltage 1100 V per IS 7098 Part 1"
    )
    std = RecommendationResultItem(
        standard_id="IS-7098-1",
        is_code="IS 7098 (Part 1)",
        title="XLPE Insulated PVC Sheathed Cables",
        department="Electro-technical",
        scope_summary="Working voltage 1100 V",
        key_specifications="1.1 kV",
        testing_requirements="High voltage test",
        status="ACTIVE",
        score=0.92,
        reason="Direct match for underground distribution"
    )
    item_eval = ItemComplianceEvaluation(
        item_id="ITEM-01",
        item_name=norm.item_name,
        normalized_profile=norm,
        standards=[std],
        primary_standard=std,
        compliance_status="COMPLIANT",
        score=0.92,
        applicable_scheme="ISI Mark (Scheme I)",
        is_mandatory_certification=True,
        missing_parameters=[],
        evidence=["Governed by IS 7098 (Part 1)"],
        recommendation="Procurement ready with standard compliance"
    )
    
    rec = SourcingRecommendationItem(
        source_id="SRC-MFR-BHEL-BHOPAL",
        source_name="BHEL Heavy Electrical Plant",
        source_type="MANUFACTURER",
        verification_status="VERIFIED",
        bis_certification_status="REQUIRES_LIVE_VERIFICATION",
        trust_score=0.88,
        trust_level="HIGH",
        location=LocationModel(city="Bhopal", state="Madhya Pradesh", latitude=23.25, longitude=77.41),
        supported_items=[norm.item_name],
        relevant_standards=["IS-7098-1"],
        suitability_score=0.90,
        confidence=0.88,
        reasoning=["Central PSU power equipment manufacturer."],
        score_breakdown=ScoreBreakdown(
            category_match=1.0, standard_match=1.0, compliance_evidence=1.0,
            location_relevance=1.0, data_confidence=1.0, overall_score=90.0
        )
    )
    
    pkg_svc = PackageEvaluationService()
    pkg_eval = pkg_svc.evaluate_package([item_eval], sourcing_recs=[rec])
    
    exp = exp_svc.generate_procurement_explanation(
        company="Zenith GreenTech",
        items=[item_eval],
        package_eval=pkg_eval,
        sourcing_recs=[rec]
    )
    
    # Must contain tri-partite demarcations
    assert len(exp.supported_by_data) > 0
    assert any("[SUPPORTED BY DATABASE]" in s or "[SUPPORTED BY EVIDENCE" in s for s in exp.supported_by_data)
    
    # Invariant: Must not contain autonomous release language
    assert "Immediate PO release permitted" not in exp.summary
    assert "automatic purchase" not in exp.summary.lower()
    
    # Must preserve verification caveats
    assert any(
        "REQUIRES LIVE VERIFICATION" in c or "manakonline.in" in c or "verification" in c.lower()
        for c in exp.inference_requires_verification + exp.compliance_caveats
    )
