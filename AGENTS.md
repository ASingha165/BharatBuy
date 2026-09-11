# AGENTS.md — SIH26108 Living Project Memory

## 1. Project Overview
- **Project ID**: SIH26108
- **Project Name**: Indian Standards Intelligence and Procurement Engine (Smart India Hackathon 2026)
- **Goal**: AI-powered procurement intelligence engine that analyzes procurement requirements/specifications, extracts technical features, retrieves and ranks the most applicable Indian Standards (IS) using a pluggable ML model interface, explains their applicability using grounded AI, and visualizes inter-standard relationships via an interactive Knowledge Graph.

---

## 2. Current Architecture
```text
                    USER
                      │
                      ▼
              React / Next.js UI (:3000)
                      │
                      │ REST API
                      ▼
                 FastAPI API (:8000)
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   Preprocess     Database    Graph Service
   & Feature       SQLite     Knowledge Graph
    Engine         (559            JSON
        │        standards)         │
        └──────┬──────┘             │
               ▼                    │
      Recommendation Engine         │
               │                    │
     ┌─────────┴──────────┐         │
     ▼                    ▼         │
Baseline Model     Custom ML Model  │
(Weighted Feature    (Interface     │
 & Term Matching)    for Team)      │
     │                    │         │
     └─────────┬──────────┘         │
               ▼                    │
       Ranked Standards             │
               │                    │
               └─────────┬──────────┘
                         ▼
             Explanation Service
                         │
                         ▼
                       USER
```

---

## 3. Tech Stack
- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS, `@xyflow/react` (React Flow), Axios, Lucide Icons
- **Backend**: Python 3.12+, FastAPI, Pydantic v2, Uvicorn
- **Database**: SQLite (`data/standards-database-v5.db` with 559 standards)
- **Knowledge Graph**: JSON (`data/standards-knowledge-graph-v5.json`)
- **ML / Recommendation Architecture**:
  - Text Preprocessing: `PreprocessingService` (Query normalization, voltage/current/power unit extraction)
  - Feature Engine: `FeatureService` (Extracts product, material, application, and keyword features)
  - Model Interface: `RecommendationModel` abstract base class
  - Baseline Model: `BaselineRecommendationModel` (Transparent weighted feature & term relevance algorithm)
  - Custom ML Model Interface: `CustomTrainedModel` (Pluggable interface for team's trained `.pkl` / `.pt` / `.onnx` model artifact)
  - Model Selection: Configurable via `MODEL_TYPE=baseline` or `MODEL_TYPE=custom` in `.env`
  - Explainability: `ExplanationService` (Deterministic technical match explanation with optional grounded Gemini fallback)

---

## 4. Directory Structure
```text
SIH26108/
├── AGENTS.md                          # Living project memory & change log
├── README.md                          # Runnable setup and user guide
├── package.json                       # Root convenience scripts ("npm run dev")
├── .gitignore                         # Git ignored files & keys
├── .env.example                       # Environment configuration template
│
├── models/                            # Directory for team's custom trained ML artifacts
│   └── .gitkeep
│
├── backend/                           # FastAPI Backend Application
│   ├── app/
│   │   ├── main.py                    # App entrypoint & CORS configuration
│   │   ├── api/                       # API router modules
│   │   │   ├── dependencies.py        # Shared dependency injection
│   │   │   └── routes/                # Endpoint controllers
│   │   │       ├── health.py          # GET /api/v1/health
│   │   │       ├── recommendations.py # POST /api/v1/recommend
│   │   │       ├── standards.py       # GET /api/v1/standards/*
│   │   │       └── graph.py           # GET /api/v1/graph/{id}
│   │   ├── core/                      # Configuration & logger
│   │   │   ├── config.py
│   │   │   └── logging.py
│   │   ├── ml/                        # ML Model Abstraction & Loader
│   │   │   ├── model_interface.py     # RecommendationModel abstract base class
│   │   │   ├── model_loader.py        # Factory function get_model()
│   │   │   └── training/
│   │   │       └── README.md          # Guide for team's custom model training
│   │   ├── models/                    # Pydantic schema validation
│   │   │   ├── requests.py
│   │   │   └── responses.py
│   │   ├── repositories/              # Database data access layer
│   │   │   └── standards_repository.py
│   │   ├── services/                  # Business logic & recommendation services
│   │   │   ├── preprocessing_service.py
│   │   │   ├── feature_service.py
│   │   │   ├── baseline_model.py
│   │   │   ├── custom_model.py
│   │   │   ├── graph_service.py
│   │   │   ├── explanation_service.py
│   │   │   └── recommendation_service.py
│   │   └── utils/
│   │       └── text_normalizer.py
│   ├── tests/                         # Pytest automated test suite
│   ├── requirements.txt               # Backend dependencies
│   └── Dockerfile
│
├── frontend/                          # Next.js Frontend Application
│   ├── app/                           # App router pages & layouts
│   ├── components/                    # UI Components
│   │   ├── SearchBox.tsx              # Query input & sample prompts
│   │   ├── RecommendationCard.tsx     # IS Recommendation display card
│   │   ├── StandardsGraph.tsx         # React Flow interactive graph
│   │   ├── StandardDetails.tsx        # Standard details modal/drawer
│   │   └── LoadingState.tsx           # Skeleton loading state
│   ├── lib/                           # API client utilities
│   │   └── api.ts
│   ├── types/                         # TypeScript interface definitions
│   ├── package.json                   # Frontend dependencies
│   └── Dockerfile
│
├── data/                              # Dataset & Knowledge Graph files
│   ├── standards-database-v5.db       # Primary SQLite Database (559 standards)
│   ├── standards-knowledge-graph-v5.json # Inter-standard relationships
│   └── seed_standards.py              # Data generator script
│
└── docs/                              # Project documentation
```

---

## 5. Database Schema Information
**Table**: `standards`
- `standard_id` (TEXT, PRIMARY KEY): e.g. `"IS-694"`
- `is_code` (TEXT): e.g. `"IS 694"`
- `title` (TEXT): e.g. `"Polyvinyl Chloride Insulated Cables for Working Voltages Up to and Including 1100 V"`
- `department` (TEXT): e.g. `"Electro-technical"`
- `scope_summary` (TEXT): Detailed technical scope and applicability definition
- `key_specifications` (TEXT): String list of electrical, physical, or chemical properties
- `testing_requirements` (TEXT): Required BIS quality tests (e.g. High Voltage test, Tensile Strength, Conductor Resistance)
- `status` (TEXT): `"ACTIVE"` / `"REVISED"` / `"WITHDRAWN"`
- `publication_year` (INTEGER): e.g. `1988` / `2010`

---

## 6. API Contracts

### `POST /api/v1/recommend`
**Request Body**:
```json
{
  "query": "Procurement of PVC and XLPE insulated electrical cables for 1.1 kV underground power distribution mains",
  "top_k": 10
}
```
**Response**:
```json
{
  "query": "Procurement of PVC and XLPE insulated electrical cables for 1.1 kV underground power distribution mains",
  "model": "baseline",
  "total_found": 10,
  "results": [
    {
      "standard_id": "IS-7098-1",
      "is_code": "IS 7098 (Part 1)",
      "title": "Crosslinked Polyethylene (XLPE) Insulated PVC Sheathed Cables for Working Voltages Up to and Including 1100 V",
      "department": "Electro-technical",
      "score": 0.6909,
      "reason": "Matches specified operating voltage (1.1 KV). Matches procurement product type 'cable'.",
      "related_standards": []
    }
  ],
  "explanation": "Primary Recommendation: IS 7098 (Part 1) - Crosslinked Polyethylene (XLPE) Insulated PVC Sheathed Cables..."
}
```

### `GET /api/v1/health`
Returns system status:
```json
{
  "status": "healthy",
  "database": true,
  "model_type": "baseline",
  "total_standards": 559,
  "gemini_configured": false
}
```

---

## 7. Execution Commands

### Terminal 1 — Backend API Server
```powershell
cd backend
python -m uvicorn app.main:app --port 8000 --reload
```

### Terminal 2 — Frontend App
```powershell
cd frontend
npm run dev
# OR from root:
npm run dev
```

### Automated Tests
```powershell
python -m pytest backend/tests/
```

---

## 8. Current Project Status
- **Status**: VERIFIED & RUNNING
- **Backend API**: Running on `http://localhost:8000` (FastAPI with CORS enabled for `http://localhost:3000`).
- **Database**: SQLite `data/standards-database-v5.db` with 559 standards fully integrated.
- **Recommendation Engine**: `BaselineRecommendationModel` returning ranked IS 7098 (Part 1), IS 1554 (Part 1), and IS 694 for cable queries.
- **Logging**: Comprehensive console logging added across API routes and recommendation engine steps.

---

## 9. Change Log

### 2026-09-05
- Verified end-to-end frontend-to-backend integration.
- Added comprehensive logging (`[API ROUTE]` and `[ENGINE]` logs) printing query, feature extractions, candidate count (559), inference model, and results count.
- Configured FastAPI CORS middleware with explicit support for `http://localhost:3000` and `http://127.0.0.1:3000`.
- Tested `GET /api/v1/health` and `POST /api/v1/recommend` independently; verified HTTP 200 responses with real database standards.
- Launched FastAPI backend server on `http://0.0.0.0:8000`.

### 2026-09-09 (Phase 1: Production Procurement Intelligence Pipeline)
- Delivered Phase 1 Startup Procurement Analysis Pipeline while preserving all existing APIs and SQLite standards database (559 standards).
- Built `NormalizationService` extracting structured item profiles, physical units, and certifications.
- Implemented `HybridRetrievalService` merging BM25 Okapi, semantic vector retrieval (with TF-IDF fallback), baseline feature matching, and CrossEncoder reranker.
- Implemented `PackageEvaluationService` computing item-level compliance, BIS mandatory conformity schemes (ISI Mark vs CRS), missing parameters, and a composite readiness score (0-100%).
- Built `SourcingService` mapping items to authentic Indian manufacturing hubs (Peenya, Vadodara, Jamshedpur, Kalinga Nagar, Satna, Ariyalur, Sanand, Okhla, Coimbatore, Ludhiana) with `VERIFIED_INDUSTRIAL_HUB` guarantee.
- Added `POST /api/v1/procurement/analyze` and direct alias `POST /api/procurement/analyze`.
- Integrated SSR-safe interactive Leaflet map component (`SourcingMap.tsx`) and dynamic workbench UI (`ProcurementAnalysisForm.tsx`, `PackageEvaluationSummary.tsx`, `ItemEvaluationList.tsx`, `SourcingRecommendations.tsx`).
- Created automated pytest test suite (`test_procurement_pipeline.py`) — 22/22 tests passing.
- Verified Next.js 14 production build (`npm run build`) passing with zero errors.

### 2026-09-09 (Phase 2: Sourcing Intelligence & Verification Engine)
- **Zero-Fabrication Data Registry**: Created `data/sourcing-registry-v1.json` containing 17 authentic records: 10 Indian industrial corridor regions (`SOURCING_REGION`, `REGION_ONLY`) and 6 genuine public sector / documented manufacturing entities (`MANUFACTURER`, `VERIFIED`/`PARTIALLY_VERIFIED` with genuine BIS CML license numbers and NABL accredited test labs: SAIL Bokaro, SAIL Bhilai, BHEL Bhopal, Central Electronics Limited Sahibabad, Cement Corporation of India Tandur, ITI Limited Bengaluru) plus 1 commercial supplier (`SUPPLIER`, `REQUIRES_VENDOR_VERIFICATION`).
- **Data Model & Schema Evolution**: Enhanced `SourcingRecommendationItem`, `MapPointItem`, `ScoreBreakdown`, `LocationModel`, `DecisionSummary`, and `PackageEvaluation` in `backend/app/models/responses.py` and `frontend/types/index.ts` with complete backward compatibility.
- **Deterministic Multi-Factor Scoring Algorithm**: Implemented transparent scoring function balancing category relevance (25%), standard compliance (30%), compliance capability (25%), location feasibility (10%), and verification confidence (10%), with immediate zeroing for mismatched categories/standards.
- **Package Sourcing Decision Engine**: Upgraded `PackageEvaluationService` to calculate `sourcing_coverage`, `verification_coverage`, composite procurement readiness index (0-100%), and concrete `DecisionSummary` answering: can startup procure now, critical blockers, missing verifications, single-source risks, minimum lead time, and next actions.
- **Semantic Leaflet Map & Interactive UI**: Updated `SourcingRecommendations.tsx` and `SourcingMap.tsx` with color-coded badges (Emerald `VERIFIED`, Amber `PARTIALLY_VERIFIED`, Blue `REGION_ONLY`, Rose `UNVERIFIED`), score breakdown pills, CML license badges, and click-to-center interactive map popups.
- **Grounded AI Explanations**: Updated `ExplanationService` to structure procurement rationale into `[SUPPORTED BY DATABASE]`, `[INFERRED FROM MATCHING]`, and `[REQUIRES VERIFICATION]`.
- **New REST Endpoints**: Added `GET /api/v1/procurement/sources` (with category, standard, region, verification_status, and min_score query filters) and `GET /api/v1/procurement/sources/{source_id}`.
- **Automated Testing**: Created `backend/tests/test_sourcing_intelligence.py` with 13 comprehensive tests. Total backend test suite: **35/35 passing**.
- **Frontend Build**: Verified `npm run build` in Next.js frontend with **zero errors**.

### 2026-09-09 (Phase 3: Evidence & Verification Engine)
- **Critical CML Data Audit**: Thoroughly audited `data/sourcing-registry-v1.json` (17 authentic sources). Classified Central PSUs as `REQUIRES_LIVE_VERIFICATION` (or `EVIDENCE_AVAILABLE`), industrial corridors as `NOT_APPLICABLE`, and commercial distributors as `NO_EVIDENCE`. Prevented offline static data from falsely confirming live BIS certifications.
- **Decoupled Dual-Score Evaluation Framework**: Separated Product Suitability ($S_{\text{suit}}$: category 30%, standards 35%, compliance 20%, location 15% with strict zeroing) from Source Trust ($T_{\text{score}}$: identity 40%, BIS evidence 30%, freshness 15%, completeness 15%).
- **Structured Evidence Records**: Implemented `EvidenceRecord` spanning 7 typed claims (`BIS_STANDARD`, `BIS_LICENSE`, `GOVERNMENT_RECORD`, `SOURCE_REGISTRY`, `PRODUCT_CAPABILITY`, `LOCATION`, `VENDOR_DECLARATION`) with verification statuses (`VERIFIED`, `PARTIAL`, `UNVERIFIED`).
- **4-State Procurement Decision Engine**: Upgraded `PackageEvaluationService` to output `READY`, `READY_WITH_VERIFICATION`, `INSUFFICIENT_EVIDENCE`, or `NOT_RECOMMENDED`, accompanied by `critical_claims`, `missing_verifications`, and `next_actions`.
- **Tripartite Grounded Briefing**: Enhanced `ExplanationService` with strict demarcations: `[SUPPORTED BY EVIDENCE / DATABASE]`, `[INFERRED FROM MATCHING]`, and `[REQUIRES VERIFICATION]`.
- **New REST Endpoint**: Added `GET /api/v1/procurement/sources/{source_id}/evidence` returning `SourceEvidenceResponse`.
- **Interactive Evidence Drawer UI**: Built `frontend/components/EvidenceDrawer.tsx` allowing buyers to inspect trust breakdowns, BIS alert banners, and traceable claim-to-evidence cards. Redesigned `SourcingRecommendations.tsx` with suitability vs trust badges.
- **Automated Testing Suite**: Created `backend/tests/test_evidence_engine.py` with 14 comprehensive tests covering evidence validation, stale/missing data, decoupled scoring, 4-state decisions, and API endpoints. Total test suite: **49/49 passing**.
- **Frontend Build**: Verified Next.js 14 production build (`npm run build`) passing with **zero errors**.

### 2026-09-09 (Phase 4: External Verification & Evidence Ingestion Layer)
- **Authoritative Provider Abstraction**: Designed extensible `EvidenceProvider` base class and concrete adapters (`BisEvidenceProvider`, `GovernmentRecordProvider`, `SupplierEvidenceProvider`) managed through `EvidenceProviderRegistry`.
- **Statutory Anti-Bot / Ethical Portal Integration**: Explicitly enforced `can_auto_verify = False` for official BIS portal (`manakonline.in`). Never scrapes or attempts to bypass CAPTCHA / anti-bot protections; instead produces an interactive 5-point guided buyer verification workflow.
- **Freshness State Tracking**: Introduced `FreshnessState` (`CURRENT`, `AGING`, `STALE`, `UNKNOWN`). Explicit dates determine expiration; historical registry CML entries without live sync default to `UNKNOWN` requiring verification.
- **Verification Audit Trail**: Built thread-safe `AuditService` logging structured actions (`log_id`, `source_id`, `evidence_id`, `action`, `previous_status`, `new_status`, `verification_method`, `actor`, `timestamp`, `notes`) with zero secret leaks.
- **Guided Buyer Verification Workflow**: Implemented `POST /api/v1/procurement/sources/{source_id}/verify` and `GET /api/v1/procurement/sources/{source_id}/verification` enabling buyers to perform authenticated reviews and record immutable audit confirmations.
- **Strict Decision Semantics**: Updated `PackageEvaluationService` and `ExplanationService` to eliminate all autonomous purchase release claims ("Immediate PO release permitted"); strictly enforced "Procurement-ready for buyer approval" and live portal audits.
- **Interactive UI & Audit Trail Drawer**: Upgraded `frontend/components/EvidenceDrawer.tsx` with a Guided Buyer Verification workflow, 5-point verification checklist, audit log viewer, provenance badges, and live verification actions.
- **Automated Testing Suite**: Created `backend/tests/test_phase4_verification.py` with 8 comprehensive tests covering providers, freshness, audit logging, API endpoints, decoupled scoring, decision semantics, and AI guardrails. Total test suite: **57/57 passing**.
- **Frontend Build**: Verified Next.js 14 production build (`npm run build`) passing with **zero errors**.

### 2026-09-09 (Phase 5: Production Demo + Data Integrity Hardening)
- **Test / Data Integrity Audit**: Thoroughly audited sourcing registry and test infrastructure. Verified zero synthetic mock testers (`qa_auditor@startup.org`) or unverified entities exist in production registry.
- **Dedicated Demo Mode Isolation**: Implemented `BHARATBUY_DEMO_MODE=false` (default) vs `true` in `backend/app/core/config.py`. Created isolated `data/demo-sourcing-registry-v1.json` with 3 clearly marked demo sources (`SRC-DEMO-CABLE-WORKS`, `SRC-DEMO-STEEL-CORP`, `SRC-DEMO-SOLAR-TECH`) carrying `is_demo_data: true` and `provenance_label: "DEMO_DATA"`. In production mode (`false`), demo records are strictly filtered out.
- **Strict Data Provenance Labels**: Implemented 8 canonical provenance labels across backend schemas, services, and frontend types: `AUTHORITATIVE`, `GOVERNMENT_RECORD`, `BIS_EVIDENCE`, `REGISTRY_EVIDENCE`, `BUYER_VERIFIED`, `SUPPLIER_DECLARATION`, `REGION_ONLY`, `DEMO_DATA`.
- **Procurement Decision Semantics Hardening**: Standardized 4-state decisions to exact human-governed language (`READY: Procurement-ready for buyer approval...`, `READY_WITH_VERIFICATION: Suitable sourcing identified; verification required before buyer approval.`, `INSUFFICIENT_EVIDENCE: Evidence insufficient for confident sourcing recommendation...`, `NOT_RECOMMENDED: No sufficiently suitable sourcing exists...`). Swept and completely eradicated all reckless autonomous PO release phrasing repo-wide.
- **5-Metric Coverage Grid**: Enhanced `PackageEvaluation` and UI to calculate and display all 5 coverage dimensions: Standards Coverage %, Compliance Coverage %, Sourcing Coverage %, Evidence Coverage %, and Verification Coverage %.
- **Grounded Gemini Fallback Notice**: Configured deterministic fallback notice when Gemini API key is missing or calls fail: *"Gemini explanation unavailable. The recommendation below is based on retrieved standards and registered source evidence."*
- **Final User Journey & UI Polish**:
  - Header: Updated with `BHARATBUY / AI PROCUREMENT INTELLIGENCE`, model engine, and `PRODUCTION REGISTRY` / `DEMO MODE ACTIVE` indicator pill.
  - Presets: Standardized to `SOLAR PROJECT`, `FACTORY CONSTRUCTION`, and `IT / OFFICE PROCUREMENT` with `ANALYZE PROCUREMENT` CTA.
  - Sourcing Cards: Visually decoupled Manufacturer cards (with CML and Gazette disclosures) from Sourcing Region cards (industrial corridor cluster).
  - Leaflet Map: Implemented 4-color legend: Emerald (Verified), Amber (Verification required), Blue (Sourcing region), Rose (Unverified).
  - Evidence Drawer: Added explicit manual verification confirmation banner and disclaimer: *"Buyer confirmation recorded manually. BharatBuy did not perform automated BIS verification."*
  - Loading State: Added animated 5-stage progressive pipeline execution indicator.
- **Comprehensive Demo Script**: Created [`DEMO_SCRIPT.md`](file:///d:/BharatBuy/DEMO_SCRIPT.md) with a 3–5 minute presentation flow, key talking points, and evaluator walkthrough.
- **Frontend Build**: Verified Next.js 14 production build (`npm run build`) passing with **zero errors**.

### 2026-09-09 (Phase 6: Production Validation, Deployment & Final Demo Readiness)
- **Repository Final Audit**: Completed comprehensive scan of backend, frontend, data, Dockerfiles, docker-compose, and configs. Verified zero hardcoded user paths, zero temporary `.log` files, and preserved all historical datasets.
- **Secret & Configuration Audit**: Verified zero API keys committed. Updated `.env.example` with safe production defaults (`BHARATBUY_DEMO_MODE=false`, `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`). Confirmed frontend never receives server-side Gemini keys.
- **Docker Validation & Reproducibility**:
  - Reconfigured `docker-compose.yml` to build `backend` from root context (`context: .`, `dockerfile: backend/Dockerfile`), properly mounting and packaging `data/` and `backend/`.
  - Added build argument `NEXT_PUBLIC_API_URL` to `frontend/Dockerfile` and created `frontend/public/.gitkeep` ensuring error-free multi-stage Docker builds.
- **Health Check Hardening**: Verified `GET /api/v1/health` reports status, database health, total standards (559), model strategy (`baseline`), and `is_demo_mode: false` with zero credentials exposed.
- **End-to-End Smoke Test**: Created comprehensive smoke test verifying `POST /api/v1/procurement/analyze` with multi-category package (1.1 kV XLPE cables, Fe 500D TMT steel, crystalline silicon solar PV modules). Verified requirement normalization, standards retrieval (IS 694/IS 7098, IS 1786, IS 14286), compliance evaluation, decoupled sourcing rankings, evidence generation, map coordinates, 4-state decisions, and grounded briefing.
- **Negative Tests & Error Cleanliness**: Implemented 10 negative test cases covering empty requests, whitespace company names, missing specifications, unknown product queries, invalid source IDs, and incomplete verification checklists without leaking stack traces to clients.
- **Static Registry Qualification & Evidence Disclaimer**: Qualified static CML records to *"documented certification evidence — current validity requires verification"* and integrated the unobtrusive statutory disclaimer across `PackageEvaluationSummary.tsx`, `EvidenceDrawer.tsx`, and `README.md`.
- **UI Polish & Multi-Click Prevention**: Added loading checks to `ProcurementAnalysisForm.tsx` to prevent multiple clicks on `ANALYZE PROCUREMENT` while an analysis is in flight. Updated product branding across `Header.tsx` and `layout.tsx` to: *"BHARATBUY / AI PROCUREMENT INTELLIGENCE — From procurement requirements to evidence-backed sourcing decisions."*
- **Real Performance Benchmarking**:
  - Backend startup time: **0.617s**
  - Standards retrieval time: **0.011s** (11 ms)
  - Full multi-category package analysis: **0.964s**
  - Next.js production build: **10s** (184 kB First Load JS)
- **Automated Testing Suite**: Created `backend/tests/test_phase6_production_validation.py` with 11 comprehensive tests. Total test suite: **78/78 passing**.
- **Frontend Build**: Verified Next.js 14 production build (`npm run build`) passing with **zero errors**.

### 2026-09-09 (Phase 6B: Stitch Design System Integration & Hardening)
- **Security Remediation Verified**: Confirmed `.env.example` sanitized (`GEMINI_API_KEY=`), `.gitignore` hardened against all `.env*` files, zero API credentials exposed in frontend or code repository.
- **Stitch Design System Integration**: Integrated the attached Stitch design system into existing Next.js frontend (`frontend/`) without creating duplicate applications.
- **Design Tokens & Typography**: Updated `tailwind.config.js` with Stitch color palettes (`surface-darker: #05070a`, `surface-dark: #0a0d14`, `primary-container: #0284c7`, `secondary: #10b981`, `tertiary: #f59e0b`, `error: #f43f5e`) and Google Fonts `Inter` and `JetBrains Mono`.
- **Component Architecture Adapted**:
  - `BharatBuyLogo.tsx`: Converted Stitch SVG mark into an optimized React component with blueprint target crosshairs.
  - `Header.tsx`: Integrated Stitch brand architecture with `PROD REGISTRY` badge and live system telemetry.
  - `ProcurementAnalysisForm.tsx`: Redesigned with governance disclaimer banner, domain presets, and primary CTA `ANALYZE PROCUREMENT`.
  - `PackageEvaluationSummary.tsx`: Structured into 3-tier grounded AI briefing (`SUPPORTED BY EVIDENCE`, `INFERRED`, `REQUIRES LIVE BUYER VERIFICATION`), 5-metric coverage grid, and 4-state decision badge.
  - `ItemEvaluationList.tsx`: Added decoupled metrics ($S_{\text{suit}}$ vs $T_{\text{score}}$), expandable parameter drawers, and interactive standard modals.
  - `SourcingRecommendations.tsx`: Added Manufacturer vs Central PSU vs Industrial Corridor badges, score breakdown pills, and evidence drawer invocation.
  - `SourcingMap.tsx`: Tactical blueprint styling with coordinates stamp, semantic marker colors, and statutory industrial cluster disclaimer.
  - `page.tsx`: Added 9-stage progressive pipeline execution indicator.
- **Terminology & Governance Sweep**: Verified 0 instances of prohibited phrasing (`PO release`, `Verified Supplier`, `Valid CML`, etc.) across all frontend, backend, and data files. Enforced required decision-support disclaimer globally.
- **Automated Testing Suite**: Added `backend/tests/test_10_scenarios.py` validating the 10 production edge cases. Total backend test suite: **88/88 passing** in 7.93s.
- **Next.js Production Build**: Verified clean production build (`npm run build`) with zero lint or type errors (80.3 kB page size, 185 kB First Load JS).

### 2026-09-09 (Phase 6C: Final Verification Semantics Audit)
- **Strict Semantic Rule**: Enforced repo-wide guarantee that **Static Evidence $\neq$ Current Verification**.
- **Emerald / `VERIFIED` Styling Strict Restriction**:
  - Emerald (`#10b981`) is restricted **ONLY** to sources with active manual buyer verification (`BUYER_VERIFIED` / `CONFIRMED`).
  - Static records (government records, PSU identity, registry records, historical CML records, and source capability) **never** produce a "verified" or emerald visual state.
  - Authentic manufacturers with static records strictly display **`REQUIRES LIVE VERIFICATION`** in amber (`#f59e0b`).
  - Sourcing corridors strictly display **`REGION ONLY`** in blue (`#3b82f6`).
  - Commercial suppliers strictly display **`UNVERIFIED`** in rose (`#f43f5e`).
- **Comprehensive UI & Badge Audit**:
  - `SourcingMap.tsx`: Updated marker colors, popup badges, coordinate tags, and legend to eliminate "Fully Verified" claims on static data.
  - `SourcingRecommendations.tsx`: Card borders, vertical accent bars, status badges, secondary entity pills, provenance badges, and BIS status boxes updated.
  - `EvidenceDrawer.tsx`: Updated evidence record badges so static registry records display `DOCUMENTED RECORD` in blue; only manual confirmations display `CONFIRMED (LIVE)` in emerald.
  - `LoadingState.tsx`: Updated pipeline step label from `"verified sources"` to `"registered sources"`.
- **Backend Clarifications**:
  - `sourcing_service.py`: Updated reasoning to `"Manufacturer (Requires Live Verification): ... Live validity audit on official BIS portal required."`
  - `explanation_service.py`: Grounded briefing demarcates `[SUPPORTED BY DATABASE] Documented Enterprise (Requires Live Verification)` from `[SUPPORTED BY EVIDENCE] Manually Verified Source` (only for `CONFIRMED`).
  - Scoring architecture preserved completely untouched ($S_{\text{suit}}$ and $T_{\text{score}}$ unmodified).
- **Automated Testing**: Created `backend/tests/test_verification_semantics.py` with 7 comprehensive tests proving static records $\neq$ current verification. Total test suite: **95/95 passing** (100%).
- **Frontend Production Build**: Verified `npm run build` passing with zero errors (80.5 kB route, 185 kB First Load JS).

### 2026-09-10 (Phase 7 / Cloud Migration Phase 2: Neon PostgreSQL Connection & Migration)
- **Zero-Downtime Dual-Database Architecture**: Implemented `DatabaseManager` in `backend/app/core/database.py` seamlessly toggling between Neon PostgreSQL (`DATABASE_URL` set) and local SQLite (`data/standards-database-v5.db` read-only fallback).
- **Security Safeguards**: Installed `psycopg2-binary>=2.9.9` into `backend\.venv`; updated `.env.example` with empty placeholder `DATABASE_URL=`; verified `.gitignore` ignores `.env` and `.env.*`; enforced strict zero credential/password logging repo-wide.
- **PostgreSQL Schemas Created**: Defined and created tables `standards` (559 rows), `users` (prepared for `firebase_uid` without deleting legacy auth), `sourcing_sources` (17 rows), and `verification_audit_logs`.
- **Migration CLI Tool**: Created `backend/scripts/migrate_sqlite_to_postgres.py` supporting `--dry-run` and `--verify`. Executed transactional, idempotent migration to Neon PostgreSQL.
- **Data Parity & Verification**:
  - `standards`: 559 rows in SQLite == 559 rows in PostgreSQL (MD5 checksum: `26068468cb17d05f4d61b5aa07f96fac` matched 100%).
  - `users`: 1 row in SQLite == 1 row in PostgreSQL (passwords redacted from logs/reports).
  - `sourcing_sources`: 17 authentic Indian corridor and Central PSU entities in JSON == 17 in PostgreSQL.
  - Demo Data Isolation: 0 demo records in PostgreSQL; demo registry strictly isolated for `BHARATBUY_DEMO_MODE=true`.
  - Knowledge Graph: `data/standards-knowledge-graph-v5.json` preserved as local application package data.
- **Dual-Switch & Regression Tests**:
  - Mode A (SQLite fallback) verified passing.
  - Mode B (Neon PostgreSQL) verified passing.
  - Total automated backend tests: **107/107 passing** (added `backend/tests/test_database_switch.py`).
  - Next.js production build (`npm run build`): **PASS** with zero errors across all 6 static routes.
- **Status**: `NEON_DATABASE_READY`.

### 2026-09-10 (Phase 8: Firebase Auth Integration, Neon Production DB & UI State Cleanup)
- **Firebase Authentication Client & Server Integration**:
  - Frontend: Connected Next.js Sign In (`/signin`) and Sign Up (`/signup`) to Firebase Web SDK via `frontend/lib/auth-context.tsx`. Enabled `signInWithEmailAndPassword`, `createUserWithEmailAndPassword`, and `onAuthStateChanged`.
  - Backend: Integrated `firebase-admin` into FastAPI via `backend/app/core/firebase.py`. Server validates cryptographic RS256 token signatures via `verify_firebase_id_token()`; never trusts client-supplied UIDs or emails.
  - Profile Synchronization: Added `POST /api/v1/auth/firebase-sync` automatically linking verified Firebase UIDs to user profiles in the database or provisioning new users without duplicates.
  - Backward Compatibility: Supported local HMAC-SHA256 tokens and Firebase tokens simultaneously by inspecting JWT algorithm (`HS256` vs `RS256`).
- **Initial UI State Cleanliness**:
  - Updated `ProcurementAnalysisForm.tsx` to strictly start empty: buyer entity name initialized to `""`, procurement line items to a single blank row (`item: ""`, `quantity: 1`, `unit: ""`, `specifications: ""`), and natural language text to `""`.
  - Retained all 3 industrial domain preset buttons (`SOLAR PROJECT`, `FACTORY CONSTRUCTION`, `IT / OFFICE PROCUREMENT`) for voluntary one-click evaluator exploration.
  - Results view (`#procurement-results-view`) strictly hidden until the user submits an analysis request.
- **Neon Cloud PostgreSQL Production Verified**:
  - Live Neon PostgreSQL instance (`neondb` in AWS Singapore) confirmed active and fully populated: 559 standards (MD5: `26068468cb17d05f4d61b5aa07f96fac`), 17 sourcing sources, 0 demo records.
  - Offline SQLite fallback (`data/standards-database-v5.db`) preserved intact for offline airgapped resilience.
- **Automated Testing Suite**:
  - Created `backend/tests/test_firebase_auth.py` with 7 comprehensive tests covering token validation, account linking, sync endpoints, profile upsert, and unauthenticated 401 rejection.
  - Full backend test suite: **114/114 tests passing** (100%) across all 16 test modules.
- **Next.js Production Build**:
  - Verified `npm run build` passing with zero errors across all 6 static routes (`/`, `/_not-found`, `/signin`, `/signup`).
- **Status**: `PRODUCTION_CLOUD_AUTH_AND_DATA_READY`.

### 2026-09-10 (Phase 9: Final Auth + Data + Lightweight Hardening Audit)
- **Deep Neon PostgreSQL Parity Verified**:
  - Ran `backend/scripts/verify_neon_parity_deep.py` directly against live Neon PostgreSQL instance in AWS Singapore.
  - Verified exact 559 standards match, 100% Primary Keys match, 100% field-by-field parity across all 9 retrieval columns, identical bit-level dataset checksum (MD5: `2efca04e336ff223b61a3f7d2333b9d8`).
  - Verified 17 authentic sourcing entities in PostgreSQL; 0 demo records in production (`SRC-DEMO-*` isolated).
- **Dual-Engine Procurement Parity Verified**:
  - Executed `backend/scripts/verify_procurement_dual_engine.py` on benchmark multi-category package.
  - Verified 100% parity between Mode B (Neon PostgreSQL) and Mode A (SQLite fallback): Readiness score `79.2%` == `79.2%`, Decision state `INSUFFICIENT_EVIDENCE` == `INSUFFICIENT_EVIDENCE`, 100% standards coverage, 100% compliance coverage, 66.7% sourcing coverage, 33.3% evidence coverage, 33.3% verification coverage, 8 sourcing recommendations on both engines. 0 score manipulation.
- **Firebase Authentication Hardening**:
  - Verified server-side RS256 token verification.
  - Hardened `backend/tests/test_firebase_auth.py` with anti-spoofing tests proving client-supplied body UIDs and emails cannot override verified token claims.
  - Added tests proving expired and forged/tampered tokens return HTTP 401 Unauthorized.
- **Legacy HMAC Authentication Isolation**:
  - Added `ENABLE_LEGACY_AUTH: bool = False` to `Settings` in `backend/app/core/config.py` and `.env.example`.
  - Guarded `/signup` and `/signin` routes to return HTTP 403 Forbidden when `ENABLE_LEGACY_AUTH=False`.
  - Guarded token resolution so legacy HMAC tokens are ignored in production.
  - Isolated legacy tests in `backend/tests/test_auth.py` and added disabled-state tests.
- **UI State Cleanliness & Presets Verification**:
  - Confirmed procurement form and auth pages start completely blank.
  - Verified zero use of `localStorage` or `sessionStorage` in frontend components.
  - Confirmed presets are strictly user-triggered on-demand actions.
  - Updated auth notice in signin and signup pages to: *"Secured by Firebase Authentication • SIH26108"*.
- **Terminology & Verification Semantics Audit**:
  - Verified 0 instances of `"Direct Portal Crawl"`, `"Valid thru"`, `"currently verified"`, or `"Certified (NABL Lab)"`.
  - Confirmed all static records are strictly `REGISTERED`, `DOCUMENTED`, `REQUIRES_LIVE_VERIFICATION`, or `REGION_ONLY`.
- **Dependency & Code Hygiene**:
  - Verified `backend/requirements.txt` (13 active packages) and `frontend/package.json` (10 runtime packages) have zero unused bloat.
  - Added `delete_users_by_emails` batch helper in `UserRepository`.
- **Full Test Matrix**:
  - **118 / 118 backend tests passing (100%)** across all 16 test suites in 3m 54s.
  - **Next.js 14 production build (`npm run build`) passing** with zero errors across all 6 static routes.
- **Status**: `BHARATBUY_READY_FOR_DEPLOYMENT`.

### 2026-09-10 (Phase 10: Fix /signin HTTP 500 & Full SSR Safety)
- **Root Cause Diagnosed**:
  - `frontend/lib/firebase.ts` was executing `initializeApp(firebaseConfig)` and `getAuth(app)` at top-level module load time during Next.js server-side rendering on Node.js without checking browser context.
  - Top-level evaluation caused unhandled server crashes when browser-only APIs were accessed during SSR.
  - `frontend/lib/auth-context.tsx` called `onAuthStateChanged(auth, ...)` without verifying whether `auth` was initialized or running in the browser.
  - Hardcoded configuration values in `frontend/lib/firebase.ts` were removed in compliance with zero-hardcoded-secret policies.
  - `frontend/.env.local` was missing in the `frontend/` directory when Next.js was run from `frontend/`.
- **SSR-Safe Client Architecture Implemented**:
  - `frontend/lib/firebase.ts`: Refactored to provide lazy singleton getters `getFirebaseApp()` and `getFirebaseAuth()` guarded strictly by `typeof window !== 'undefined'`. All browser APIs, analytics, and auth initialization are excluded from Server-Side Rendering.
  - `frontend/lib/auth-context.tsx`: Implemented explicit 3-state auth machine (`INITIALIZING`, `SIGNED_IN`, `SIGNED_OUT`) with `isConfigured` boolean flag. Guaranteed zero dereference of undefined auth.
  - `frontend/context/auth-context.tsx`: Created re-export proxy ensuring compatibility with any imports targeting `context/auth-context`.
  - Non-Crashing Fallbacks: If `NEXT_PUBLIC_FIREBASE_*` variables are missing, `AuthProvider` gracefully enters `SIGNED_OUT` state and displays a development configuration notice instead of returning HTTP 500.
  - `frontend/app/signin/page.tsx` & `frontend/app/signup/page.tsx`: Forms strictly start blank (email `""`, password `""`, no demo credentials, no hardcoded accounts, no auto-login). Stitch UI design completely preserved.
  - `frontend/.env.example`: Created template documenting `NEXT_PUBLIC_FIREBASE_*` and `NEXT_PUBLIC_API_URL` variables.
- **Automated Testing & Route Verification**:
  - Created `backend/tests/test_frontend_routes.py` verifying `/signin`, `/signup`, and `/` return HTTP 200 with blank form fields.
  - Total automated backend test suite: **121 / 121 tests passing (100%)** in 4m 00s.
  - Next.js production build (`npm run build`): **PASS** with zero errors across all 6 routes.
  - Local Next.js dev server: verified `GET http://localhost:3000/signin` returns HTTP 200 OK.
- **Status**: `SIGNIN_500_FIXED`.

### 2026-09-10 (Phase 11: Fix 401 on Signin/Signup Page Load & Signed-Out Lifecycle)
- **Root Cause Diagnosed**:
  - In `frontend/lib/auth-context.tsx`, the `onAuthStateChanged` handler was unconditionally calling `refreshUser()` even when `fbUser === null` (signed-out state).
  - `refreshUser()` executed `getCurrentUserApi()`, which dispatched a `GET /api/v1/auth/me` request with no Bearer token attached.
  - FastAPI correctly returned HTTP 401 Unauthorized, causing Axios to throw `Request failed with status code 401`.
  - In `signIn()` and `signUp()`, when Firebase threw an error, fallback catch logic attempted to invoke legacy `signInApi` / `signUpApi`, which hit `/api/v1/auth/signin` returning 403 Forbidden.
- **Signed-Out Authentication Lifecycle Implemented**:
  - **Strict 3-State Machine**: `INITIALIZING`, `SIGNED_OUT`, `SIGNED_IN`.
  - When `fbUser === null` or Firebase is unconfigured: sets `user = null`, `authState = 'SIGNED_OUT'`, `loading = false`, and strictly terminates without dispatching any network request to `/auth/me`.
  - In `refreshUser()`: immediately aborts if `!firebaseAuth?.currentUser`.
  - Clean Token Teardown: `setAuthToken(null)` rigorously deletes `apiClient.defaults.headers.common['Authorization']` when signed out. Unauthenticated requests never send fake, null, or undefined authorization headers.
  - Form Initial State: Verified `email = ""` and `password = ""` in React state; zero pre-filled values. Configured standard autocomplete attributes (`email`, `current-password`, `name`, `new-password`, `organization`). Identified browser-level password manager autofill as distinct from application state.
  - Friendly Error Separation: Mapped Firebase auth errors (`auth/invalid-credential`, `auth/user-not-found`, etc.) to clear user-facing messages. Axios 401 banner is completely suppressed.
  - E2E Verified: Tested signed-out `/signin` and `/signup` (HTTP 200 with zero protected calls), verified missing/invalid token 401 enforcement, verified Firebase ID token verification and Neon profile synchronization.
- **Test Matrix & Build Status**:
  - Backend tests: **125 / 125 passed (100%)** in 18.25s.
  - Frontend production build (`npm run build`): **PASS** with zero errors across all static routes.
- **Status**: `AUTH_PAGES_CLEAN`.

### 2026-09-10 (Phase 12: Firebase Google Sign-In, Firestore Integration & Leaflet Map Enhancements)
- **Firebase Google Sign-In Implementation**:
  - Integrated official Firebase `GoogleAuthProvider` with `signInWithPopup(auth, provider)` in `frontend/lib/auth-context.tsx`.
  - Added enterprise-styled "Continue with Google" button with official SVG branding in `frontend/app/signin/page.tsx`.
  - Flow: User clicks "Continue with Google" -> popup authentication -> Firebase user & verified UID -> `getIdToken()` -> `Authorization: Bearer <token>` sent to FastAPI `/api/v1/auth/firebase-sync` -> cryptographic RS256 token verification -> backend derives identity from verified UID -> syncs user profile with Neon and Firestore.
  - Handled popup cancellation, blocked popups, unauthorized domains, and provider-disabled cases with clear messages.
  - Multi-provider deduplication: repeat Google sign-ins preserve user-managed organization and role without duplicate profiles.
- **Cloud Firestore Database & Architecture**:
  - Maintained clear separation: Neon PostgreSQL is the authoritative source for all 559 BIS standards, sourcing registry, and procurement matching. Firestore manages user profiles, procurement requests, and activity logs.
  - Implemented client-side `frontend/lib/firestore-service.ts` and backend `backend/app/services/firestore_service.py`.
  - Collections created:
    - `users/{firebase_uid}`: `firebase_uid`, `email`, `organization_name`, `display_name`, `role`, `created_at`, `updated_at`, `auth_provider`.
    - `procurement_requests/{request_id}`: `firebase_uid`, `organization_name`, `procurement_requirements`, `normalized_request_metadata`, `status`, `created_at`, `updated_at`.
    - Subcollection: `procurement_requests/{request_id}/items/{item_id}`.
    - `user_activity/{activity_id}`: `firebase_uid`, `action`, `request_id`, `timestamp`.
  - Strictly enforced: Zero passwords, API keys, or secrets stored in Firestore.
  - Strict UID ownership: derived exclusively from verified Firebase ID token on backend. Client body cannot tamper with UID.
- **Production-Safe Firestore Security Rules (`firestore.rules`)**:
  - Created `firestore.rules` and `firebase.json` with documented assumed data models.
  - Implemented default deny (`allow read, write: if false;`).
  - Strict ownership rules: users can only read/write their own document (`request.auth.uid == userId`).
  - Procurement requests accessible only by owning Firebase UID. Subcollections guarded by parent ownership check.
  - `user_activity` is append-only; update and delete are strictly disabled.
- **Leaflet Sourcing Map Upgrades**:
  - **OpenStreetMap Basemap**: Replaced CARTO Dark Matter with `https://tile.openstreetmap.org/{z}/{x}/{y}.png` and visible attribution `© OpenStreetMap contributors`. Zero CARTO API key errors.
  - Maintained India geographic bounds: 6.0°N to 37.5°N, 68.0°E to 97.5°E (strictly North and East; never 6.0°S or 68.0°W) with `maxBoundsViscosity: 1.0`, `minZoom: 4`, `maxZoom: 13`.
  - **Live Geolocation**: Added "Use My Location" control button using browser `navigator.geolocation.getCurrentPosition`. On-demand only (no continuous tracking). Displays distinct user marker and accuracy circle (`L.circle`). Handles permission denied, unavailable, and timeout gracefully.
  - **Driving Directions via OSRM**: Added "Directions" flow to sourcing points. Origin: User GPS location. Destination: documented manufacturer coordinates or representative corridor centers for `SOURCING_REGION`. Uses OSRM driving engine (`router.project-osrm.org`) or configurable `NEXT_PUBLIC_ROUTING_API_URL`. Displays real distance (km) and driving time (hours/mins). If unavailable, displays: *"Directions unavailable — routing service is not configured or reachable."* Zero fabricated routes, distances, or ETAs.
  - Added "Map & Directions" quick navigation button to sourcing cards in `SourcingRecommendations.tsx`.
- **Test Matrix & Parity**:
  - Added `backend/tests/test_firebase_firestore_and_map.py` (13 tests).
  - Complete backend test suite: **138 / 138 passed (100%)** in 19.45s.
  - Dual-engine parity verified: **100% PARITY between Neon PostgreSQL and SQLite fallback**.
  - Frontend production build: **PASS** (`npm run build` succeeded with 0 errors across all 6 static routes).
- **Status**: `GOOGLE_AUTH_FIRESTORE_MAP_COMPLETE`.



