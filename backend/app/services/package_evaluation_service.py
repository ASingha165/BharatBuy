import re
from typing import List, Dict, Any, Tuple, Optional
from backend.app.models.responses import (
    NormalizedRequirementItem,
    ItemComplianceEvaluation,
    PackageEvaluation,
    RecommendationResultItem,
    SourcingRecommendationItem,
    DecisionSummary
)

# Mandatory conformity scheme mappings under BIS Quality Control Orders (QCO)
CRS_CATEGORIES = {"electronics", "it", "solar", "inverter", "computer", "ups", "battery", "laptop"}
ISI_CATEGORIES = {"cable", "steel", "cement", "concrete", "pipe", "fire", "extinguisher", "transformer"}

class PackageEvaluationService:
    """
    Evaluates item-level compliance and packages holistic procurement feasibility.
    Computes transparent coverage, technical parameters, sourcing coverage, and readiness index.
    """

    def evaluate_item_compliance(
        self,
        item_id: str,
        normalized: NormalizedRequirementItem,
        matching_standards: List[RecommendationResultItem]
    ) -> ItemComplianceEvaluation:
        primary_std = matching_standards[0] if matching_standards else None
        top_score = primary_std.score if primary_std else 0.0

        category_lower = normalized.category.lower()
        spec_lower = normalized.specifications.lower()

        # Determine applicable BIS conformity scheme
        is_crs = any(c in category_lower or c in spec_lower for c in CRS_CATEGORIES)
        is_isi = any(c in category_lower or c in spec_lower for c in ISI_CATEGORIES)

        if is_crs:
            scheme = "CRS (Compulsory Registration Scheme)"
            mandatory = True
        elif is_isi:
            scheme = "ISI Mark (Scheme I)"
            mandatory = True
        else:
            scheme = "Voluntary BIS Standard Conformity"
            mandatory = False

        # Identify missing technical parameters
        missing_params: List[str] = []
        if "cable" in category_lower or "cable" in spec_lower:
            has_voltage_num = bool(re.search(r'\b\d+(?:\.\d+)?\s*(?:kv|kilo\s*volts?|v|volts?)\b', spec_lower))
            if not has_voltage_num:
                missing_params.append("Operating voltage rating (e.g., 1.1 kV / 1100 V or 11 kV)")
            has_material = bool(re.search(r'\b(pvc|xlpe|copper|aluminium|aluminum|cu|al)\b', spec_lower))
            if not has_material:
                missing_params.append("Conductor/insulation material (e.g., XLPE/PVC, Copper or Aluminium)")

        if "steel" in category_lower or "rebar" in spec_lower:
            if not any(g in spec_lower for g in ["fe 415", "fe 500", "fe 550", "fe 600"]):
                missing_params.append("Steel yield strength grade (e.g., Fe 500 or Fe 550D per IS 1786)")

        if "cement" in category_lower or "concrete" in spec_lower:
            if not any(c in spec_lower for c in ["ppc", "opc", "43", "53", "m20", "m25", "m30", "grade"]):
                missing_params.append("Cement grade / compressive strength design target (e.g. PPC, OPC 43/53, M25)")

        if "solar" in category_lower:
            if not any(w in spec_lower for w in ["watt", "wp", "kw", "crystalline", "mono", "poly"]):
                missing_params.append("PV module peak wattage (Wp) and cell chemistry (Crystalline Silicon)")

        # Grounded evidence extraction from primary standard
        evidence: List[str] = []
        if primary_std:
            evidence.append(f"Standard Identified: {primary_std.is_code} ({primary_std.title})")
            if primary_std.key_specifications:
                evidence.append(f"Governing Parameters: {primary_std.key_specifications}")
            if primary_std.testing_requirements:
                evidence.append(f"Mandated Quality Verification: {primary_std.testing_requirements}")
            if primary_std.reason:
                evidence.append(f"Match Evidence: {primary_std.reason}")

        # Compute transparent status & score
        if top_score >= 0.65 and len(missing_params) == 0:
            status = "COMPLIANT"
            adj_score = round(top_score, 4)
            recommendation = f"Item is fully grounded in {primary_std.is_code}. Ensure vendor supplies BIS test certificate."
        elif top_score >= 0.40:
            status = "CONDITIONAL_COMPLIANCE"
            # Slight adjustment if critical parameters are missing
            penalty = 0.05 * len(missing_params)
            adj_score = round(max(top_score - penalty, 0.35), 4)
            rec_detail = f"Refer to {primary_std.is_code}." if primary_std else "Specify requirements."
            if missing_params:
                recommendation = f"{rec_detail} Action needed: clarify {', '.join(missing_params)} before tender issuance."
            else:
                recommendation = f"{rec_detail} Verify compliance with testing clauses."
        else:
            status = "ACTION_REQUIRED"
            adj_score = round(max(top_score, 0.15), 4)
            recommendation = "Low standard alignment. Provide detailed technical specifications or product nomenclature."

        return ItemComplianceEvaluation(
            item_id=item_id,
            item_name=normalized.item_name,
            normalized_profile=normalized,
            standards=matching_standards,
            primary_standard=primary_std,
            compliance_status=status,
            score=adj_score,
            applicable_scheme=scheme,
            is_mandatory_certification=mandatory,
            missing_parameters=missing_params,
            evidence=evidence,
            recommendation=recommendation
        )

    def evaluate_package(
        self,
        items: List[ItemComplianceEvaluation],
        sourcing_recs: Optional[List[SourcingRecommendationItem]] = None
    ) -> PackageEvaluation:
        total = len(items)
        if total == 0:
            return PackageEvaluation(
                overall_readiness_score=0.0,
                readiness_level="LOW",
                total_items=0,
                item_coverage=0.0,
                standards_coverage=0.0,
                compliance_coverage=0.0,
                sourcing_coverage=0.0,
                verification_coverage=0.0,
                sourcing_feasibility="UNAVAILABLE",
                supplier_overlap_count=0,
                decision_summary=DecisionSummary(
                    all_standards_covered=False,
                    compliant_sourcing_available=False,
                    strong_sourcing_items=[],
                    verification_required_items=[],
                    insufficient_evidence_items=[],
                    procurement_ready=False,
                    summary_text="No items provided in procurement request."
                ),
                unresolved_issues=["No items submitted in procurement request."],
                action_items=["Add procurement line items to begin analysis."]
            )

        high_conf_items = sum(1 for i in items if i.score >= 0.60)
        has_std_items = sum(1 for i in items if i.primary_standard is not None)
        compliant_items = sum(1 for i in items if i.compliance_status in ["COMPLIANT", "CONDITIONAL_COMPLIANCE"])

        item_cov = round(high_conf_items / total, 4)
        std_cov = round(has_std_items / total, 4)
        comp_cov = round(compliant_items / total, 4)

        # Compute Sourcing, Verification, and Evidence Coverage
        sourcing_recs = sourcing_recs or []
        items_with_sourcing: List[str] = []
        strong_sourcing_items: List[str] = []
        verification_required_items: List[str] = []
        insufficient_evidence_items: List[str] = []
        items_with_evidence: List[str] = []

        for itm in items:
            # Find matching sources for this item
            matching_sources = [
                r for r in sourcing_recs
                if itm.item_name in r.supported_items or any(itm.item_name.lower() in s.lower() for s in r.supported_items)
            ]
            if matching_sources:
                items_with_sourcing.append(itm.item_name)
                # Check if at least one documented manufacturer record exists
                if any(r.verification_status in ["VERIFIED", "PARTIALLY_VERIFIED"] for r in matching_sources):
                    strong_sourcing_items.append(itm.item_name)
                else:
                    verification_required_items.append(itm.item_name)

                # Check if at least one authoritative / documented evidence source exists
                if any(
                    getattr(r, "provenance_label", None) in ["AUTHORITATIVE", "GOVERNMENT_RECORD", "BIS_EVIDENCE", "BUYER_VERIFIED"]
                    or r.verification_status in ["VERIFIED", "PARTIALLY_VERIFIED"]
                    or r.bis_certification_status == "CONFIRMED"
                    for r in matching_sources
                ):
                    items_with_evidence.append(itm.item_name)
            else:
                insufficient_evidence_items.append(itm.item_name)

        sourcing_cov = round(len(items_with_sourcing) / total, 4)
        verification_cov = round(len(strong_sourcing_items) / total, 4)
        evidence_cov = round(len(items_with_evidence) / total, 4) if total > 0 else 0.0

        # Composite readiness index (0 - 100)
        # Methodology:
        # 30% Standards coverage + 30% Compliance coverage + 25% Sourcing coverage + 15% Verification coverage
        base_readiness = (
            std_cov * 30.0 +
            comp_cov * 30.0 +
            sourcing_cov * 25.0 +
            verification_cov * 15.0
        )

        # Penalize for missing critical engineering parameters
        total_missing_params = sum(len(i.missing_parameters) for i in items)
        action_required_count = sum(1 for i in items if i.compliance_status == "ACTION_REQUIRED")
        penalties = (total_missing_params * 2.5) + (action_required_count * 8.0)

        readiness_score = round(max(base_readiness - penalties, 10.0 if total > 0 else 0.0), 1)
        readiness_score = min(readiness_score, 100.0)

        if readiness_score >= 75.0:
            level = "HIGH"
            feasibility = "EXCELLENT — Clear BIS standards, documented manufacturer records, and industrial clusters established across all line items."
        elif readiness_score >= 50.0:
            level = "MODERATE"
            feasibility = "FEASIBLE — Majority of items mapped to BIS standards; supplier verification and minor parameter clarifications required."
        else:
            level = "LOW"
            feasibility = "NEEDS_SPECIFICATION — Ambiguous technical parameters or unverified sourcing evidence require refinement prior to tender."

        # Aggregate unresolved issues & actionable next steps
        unresolved: List[str] = []
        action_items: List[str] = []

        for idx, itm in enumerate(items, 1):
            if itm.missing_parameters:
                unresolved.append(f"Item #{idx} ({itm.item_name}): Clarify {', '.join(itm.missing_parameters)}.")
            if itm.compliance_status == "ACTION_REQUIRED":
                unresolved.append(f"Item #{idx} ({itm.item_name}): No high-confidence Indian Standard identified.")

        if verification_required_items:
            action_items.append(
                f"Obtain vendor BIS CML licenses for regional cluster items: {', '.join(verification_required_items)}."
            )

        if comp_cov == 1.0 and not unresolved and readiness_score >= 75.0:
            action_items.append("Procurement package is ready. Generate Request for Quotation (RFQ) incorporating cited IS codes.")
        else:
            action_items.append("Incorporate explicit BIS testing clauses from recommended standards into tender documents.")
            if unresolved:
                action_items.append("Address missing technical parameters to prevent vendor delivery mismatches.")
        action_items.append("Mandate vendor provision of NABL-accredited test certificates referencing the cited Indian Standards.")

        # Determine 4-state Procurement Decision Status
        # States: READY | READY_WITH_VERIFICATION | INSUFFICIENT_EVIDENCE | NOT_RECOMMENDED
        has_confirmed_bis = any(r.bis_certification_status == "CONFIRMED" for r in sourcing_recs)
        missing_verifications: List[str] = []
        critical_claims: List[Dict[str, Any]] = [
            {
                "claim": "All procurement items mapped to indexed Indian Standards",
                "evidence_type": "BIS_STANDARD",
                "status": "VERIFIED" if std_cov == 1.0 else ("PARTIAL" if std_cov > 0 else "UNVERIFIED"),
                "sufficient": (std_cov == 1.0)
            },
            {
                "claim": "Eligible sourcing channels discovered across manufacturing corridors",
                "evidence_type": "PRODUCT_CAPABILITY",
                "status": "VERIFIED" if sourcing_cov == 1.0 else ("PARTIAL" if sourcing_cov > 0 else "UNVERIFIED"),
                "sufficient": (sourcing_cov >= 0.80)
            },
            {
                "claim": "Direct statutory BIS CML license verified on official portal" if has_confirmed_bis else "Statutory BIS CML license documented in registry (requires live portal verification)",
                "evidence_type": "BIS_LICENSE",
                "status": "CONFIRMED" if has_confirmed_bis else "PARTIAL",
                "sufficient": has_confirmed_bis,
                "note": "Verified by buyer via official BIS portal" if has_confirmed_bis else "Verification required on official BIS portal (manakonline.in) before buyer approval"
            }
        ]

        if verification_required_items:
            missing_verifications.append(
                f"Verify individual vendor CML licenses on BIS portal for regional cluster items: {', '.join(verification_required_items)}"
            )
        
        has_unconfirmed_mfr = any(
            r.bis_certification_status in ["REQUIRES_LIVE_VERIFICATION", "EVIDENCE_AVAILABLE", "NO_EVIDENCE"]
            for r in sourcing_recs if r.source_type == "MANUFACTURER"
        )
        if strong_sourcing_items and has_unconfirmed_mfr:
            missing_verifications.append(
                "Verify live operational CML license validity on official BIS portal (manakonline.in) for primary manufacturers prior to buyer approval"
            )
        if unresolved:
            missing_verifications.append(
                f"Technical parameter resolution required for: {'; '.join(unresolved[:2])}"
            )

        if std_cov == 0.0 or sourcing_cov == 0.0 or readiness_score < 35.0:
            decision_status = "NOT_RECOMMENDED"
            can_procure_now = False
            procurement_ready = False
            decision_text = "Package Decision: NOT RECOMMENDED. No sufficiently suitable sourcing exists or mandatory compliance requirements cannot be satisfied."
        elif std_cov < 0.70 or sourcing_cov < 0.70 or len(insufficient_evidence_items) > 0 or readiness_score < 50.0:
            decision_status = "INSUFFICIENT_EVIDENCE"
            can_procure_now = False
            procurement_ready = False
            decision_text = "Package Decision: INSUFFICIENT EVIDENCE. Evidence insufficient for confident sourcing recommendation. Resolve pending specifications or sourcing gaps."
        elif len(missing_verifications) > 0 or len(unresolved) > 0 or verification_cov < 1.0 or not has_confirmed_bis:
            decision_status = "READY_WITH_VERIFICATION"
            can_procure_now = True
            procurement_ready = False
            decision_text = "Package Decision: READY WITH VERIFICATION. Suitable sourcing identified; verification required before buyer approval."
        else:
            decision_status = "READY"
            can_procure_now = True
            procurement_ready = True
            decision_text = "Package Decision: READY. Procurement-ready for buyer approval. All mandatory standards identified and verified sourcing established."

        all_stds_covered = (std_cov == 1.0)
        compliant_sourcing = (sourcing_cov == 1.0)

        decision_summary = DecisionSummary(
            decision_status=decision_status,
            can_procure_now=can_procure_now,
            all_standards_covered=all_stds_covered,
            compliant_sourcing_available=compliant_sourcing,
            strong_sourcing_items=strong_sourcing_items,
            verification_required_items=verification_required_items,
            insufficient_evidence_items=insufficient_evidence_items,
            critical_claims=critical_claims,
            missing_verifications=missing_verifications,
            recommended_actions=action_items,
            procurement_ready=procurement_ready,
            summary_text=decision_text
        )

        return PackageEvaluation(
            overall_readiness_score=readiness_score,
            readiness_level=level,
            decision_status=decision_status,
            total_items=total,
            item_coverage=item_cov,
            standards_coverage=std_cov,
            compliance_coverage=comp_cov,
            sourcing_coverage=sourcing_cov,
            verification_coverage=verification_cov,
            evidence_coverage=evidence_cov,
            sourcing_feasibility=feasibility,
            supplier_overlap_count=max(1, len(sourcing_recs)),
            decision_summary=decision_summary,
            unresolved_issues=unresolved,
            action_items=action_items
        )

