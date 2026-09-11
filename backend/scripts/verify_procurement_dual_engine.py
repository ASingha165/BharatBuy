import os
import sys
import json

sys.path.insert(0, os.path.abspath("."))
from backend.app.core.config import settings
from backend.app.core.database import db_manager
from backend.app.models.requests import ProcurementAnalysisRequest, ProcurementRequirementItem
from backend.app.api.dependencies import procurement_service

def test_procurement_scenario(engine_label: str):
    print(f"\n--- EXECUTING PIPELINE ON: {engine_label} ---")
    print(f"Active DB Engine: {db_manager.engine_name} (is_postgres: {db_manager.is_postgres})")

    req = ProcurementAnalysisRequest(
        company="GreenEarth Energy & Infra Ltd",
        requirements=[
            ProcurementRequirementItem(
                item="1.1 kV XLPE insulated underground electrical cables",
                quantity=1000,
                unit="meters",
                specifications="Working voltage 1100 V, XLPE insulation, galvanized steel armor, PVC outer sheath per IS 7098 Part 1"
            ),
            ProcurementRequirementItem(
                item="Fe 500 High strength deformed TMT steel reinforcement bars",
                quantity=45,
                unit="metric tonnes",
                specifications="TMT rebar 12mm and 16mm per IS 1786, yield strength 500 MPa, ISI mark certified"
            ),
            ProcurementRequirementItem(
                item="Crystalline silicon terrestrial solar PV modules",
                quantity=300,
                unit="units",
                specifications="Terrestrial photovoltaic modules, 450W peak, IS 14286 qualified and CRS certified"
            )
        ],
        top_k_per_item=5
    )

    result = procurement_service.analyze(req)

    summary = {
        "engine": engine_label,
        "is_postgres": db_manager.is_postgres,
        "item_count": len(result.items),
        "items": [],
        "readiness_score": result.package_evaluation.overall_readiness_score,
        "decision_state": result.package_evaluation.decision_summary.decision_status if result.package_evaluation.decision_summary else result.package_evaluation.decision_status,
        "coverage_metrics": {
            "standards_coverage": result.package_evaluation.standards_coverage,
            "compliance_coverage": result.package_evaluation.compliance_coverage,
            "sourcing_coverage": result.package_evaluation.sourcing_coverage,
            "evidence_coverage": result.package_evaluation.evidence_coverage,
            "verification_coverage": result.package_evaluation.verification_coverage
        },
        "sourcing_count": len(result.recommendations),
        "top_sourcing_id": result.recommendations[0].source_id if result.recommendations else None,
        "top_sourcing_suitability": result.recommendations[0].suitability_score if result.recommendations else None,
        "top_sourcing_trust": result.recommendations[0].trust_score if result.recommendations else None,
    }

    for item_eval in result.items:
        summary["items"].append({
            "item_name": item_eval.item_name,
            "category": item_eval.normalized_profile.category,
            "primary_standard_id": item_eval.primary_standard.standard_id if item_eval.primary_standard else None,
            "primary_is_code": item_eval.primary_standard.is_code if item_eval.primary_standard else None,
            "scheme": item_eval.applicable_scheme,
            "compliance_status": item_eval.compliance_status
        })

    print(f"Readiness Score:  {summary['readiness_score']}%")
    print(f"Decision State:   {summary['decision_state']}")
    print(f"Coverage Grid:    {summary['coverage_metrics']}")
    print(f"Sourcing Sources: {summary['sourcing_count']}")
    for i, it in enumerate(summary["items"]):
        print(f"   Item {i+1}: {it['item_name'][:35]} -> {it['primary_is_code']} ({it['scheme']})")

    return summary


def run_dual_engine_audit():
    print("=" * 70)
    print("BHARATBUY AUDIT 2: PROCUREMENT ENGINE PARITY (NEON VS SQLITE)")
    print("=" * 70)

    # 1. Test Mode B: Neon PostgreSQL
    neon_res = test_procurement_scenario("Mode B: Neon PostgreSQL Cloud Database")

    # 2. Switch to Mode A: SQLite Fallback
    try:
        db_manager._force_sqlite = True
        sqlite_res = test_procurement_scenario("Mode A: Local SQLite Fallback Database")
    finally:
        db_manager._force_sqlite = False

    # 3. Compare Results
    print("\n--- COMPARISON & PARITY VERIFICATION ---")
    assert neon_res["item_count"] == sqlite_res["item_count"] == 3, "Item count mismatch"
    assert neon_res["decision_state"] == sqlite_res["decision_state"], "Decision state mismatch"
    assert neon_res["readiness_score"] == sqlite_res["readiness_score"], "Readiness score mismatch"

    # Compare standards identified per item
    for i in range(3):
        neon_item = neon_res["items"][i]
        sq_item = sqlite_res["items"][i]
        print(f"Item {i+1} Standard Match: Neon={neon_item['primary_is_code']} | SQLite={sq_item['primary_is_code']}")
        assert neon_item["primary_standard_id"] == sq_item["primary_standard_id"], f"Standard mismatch on item {i}"
        assert neon_item["scheme"] == sq_item["scheme"], f"Scheme mismatch on item {i}"

    # Compare coverage grid
    assert neon_res["coverage_metrics"] == sqlite_res["coverage_metrics"], "Coverage metrics mismatch"

    print("\n" + "=" * 70)
    print("[SECTION 2 AUDIT RESULT] PASS: 100% PROCUREMENT ENGINE PARITY VERIFIED")
    print("=" * 70)


if __name__ == "__main__":
    run_dual_engine_audit()
