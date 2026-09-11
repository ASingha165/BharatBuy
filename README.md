# BHARATBUY — AI PROCUREMENT INTELLIGENCE (SIH26108)
> *"From procurement requirements to evidence-backed sourcing decisions."*

AI-powered procurement intelligence engine that analyzes procurement specifications, extracts technical requirements (products, materials, operating voltages/currents, standards scope), retrieves and ranks applicable Indian Standards (IS), verifies statutory conformity schemes (ISI Mark / CRS), discovers eligible Indian manufacturing sources, evaluates overall package feasibility, and visualizes inter-standard relationships via an interactive Knowledge Graph.

---

## Architecture Overview

```text
                 FRONTEND
          Next.js 14 / React 18 / TypeScript / React Flow
                    │
                    │ REST API
                    ▼
                 FASTAPI
                    │
          ┌─────────┼──────────┐
          │         │          │
          ▼         ▼          ▼
     Preprocess   Database   Graph Service
     & Feature    SQLite     Knowledge Graph
       Engine    (559+ stds)     JSON
          │         │          │
          └────┬────┘          │
               ▼               │
       Recommendation Engine   │
               │               │
       ┌───────┴────────┐      │
       ▼                ▼      │
 Baseline Model   Custom ML Model
(Weighted Feature  (Interface  │
 & Term Relevance)  for Team)  │
       │                │      │
       └───────┬────────┘      │
               ▼               │
        Final Ranking          │
               │               │
               └───────┬───────┘
                       ▼
              Explanation Layer
                       │
                       ▼
             Grounded Results & UI
```

---

## Pluggable ML Strategy (`MODEL_TYPE`)

The engine provides a clean **`RecommendationModel` interface**:

1. **`BaselineRecommendationModel`** (Active Default):
   - Fast, transparent feature matching algorithm. Evaluates product types, technical specification ratings (e.g. 1.1 kV, 1100 V), and field-level relevance across standard titles, scopes, and testing requirements.

2. **`CustomTrainedModel`** (Pluggable for Team's ML Model):
   - Reserved interface for your team's custom trained ML model.
   - Place trained artifact in `models/custom_recommendation_model.pkl` and set `MODEL_TYPE=custom` in `.env`.
   - See [`backend/app/ml/training/README.md`](file:///d:/SIH/backend/app/ml/training/README.md) for data preparation and training instructions.

---

## Quick Start Guide

### 1. Prerequisites
- Python 3.12+
- Node.js 18+ & npm

### 2. Backend Setup
```powershell
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Start FastAPI dev server
python -m uvicorn app.main:app --port 8000 --reload
```

Backend API Docs will be available at: `http://localhost:8000/api/v1/docs`

### 3. Frontend Setup
```powershell
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Next.js dev server
npm run dev
```
---

## Phase 2: Sourcing Intelligence Architecture

BharatBuy delivers a zero-fabrication **Sourcing Intelligence Engine** providing end-to-end procurement decision support:

```text
Startup Requirements
         ↓
BIS / Indian Standards
         ↓
Eligible Source & Supplier Discovery
         ↓
Supplier Verification Evidence (BIS CML / Statutory Gazettes)
         ↓
Suitability Ranking (Multi-factor Transparent Scoring)
         ↓
Geographic Visualization (Semantic Leaflet Markers)
         ↓
Procurement Decision & Grounded AI Briefing
```

### Source Verification Model & Provenance

BharatBuy adheres to a strict **Zero-Fabrication Data Integrity Rule**: no fictitious suppliers or fabricated BIS licenses are ever generated. The sourcing directory (`data/sourcing-registry-v1.json`) explicitly differentiates between geographic manufacturing corridors and authenticated corporate organizations:

| Source Type | Verification Status | Meaning & Provenance |
| :--- | :--- | :--- |
| `MANUFACTURER` | `VERIFIED` | Statutory BIS licensee / Central Public Sector Undertaking (e.g. SAIL, BHEL, CEL, CCI) with documented CML license numbers and NABL testing scope. |
| `MANUFACTURER` | `PARTIALLY_VERIFIED` | Established central enterprise (e.g. ITI Limited) with verified product domain capability; buyer verification recommended for tender-specific schedules. |
| `SOURCING_REGION` | `REGION_ONLY` | State industrial development estate (KIADB, GIDC, IDCO, DSIIDC). Represents regional manufacturing density; individual vendor CML audit required. |
| `DISTRIBUTOR` | `REQUIRES_VENDOR_VERIFICATION` | Commercial stocking channel. Original manufacturer mill test certificate and BIS license must be audited before contract award. |
| `UNKNOWN_SOURCE` | `UNVERIFIED` | Third-party prospective supplier without verified quality evidence. |

### Supplier Suitability Scoring Methodology

Suitability scores are deterministic, transparent, and non-arbitrary. Each recommendation returns full score components:

$$\text{Suitability Score} = \left( 0.25 \times \text{Category} + 0.30 \times \text{Standard} + 0.25 \times \text{Compliance} + 0.10 \times \text{Location} + 0.10 \times \text{Confidence} \right) \times 100$$

- **Category Match (0-1.0)**: Evaluates semantic alignment between normalized item category and supplier manufacturing specialization.
- **Standard Match (0-1.0)**: Direct overlap between retrieved BIS standards (`IS-1786`, `IS-7098-1`, `IS-14286`, etc.) and manufacturer scope.
- **Compliance Evidence (0-1.0)**: `VERIFIED` (1.0), `PARTIALLY_VERIFIED` (0.75), `REGION_ONLY` (0.50), `REQUIRES_VENDOR_VERIFICATION` (0.35), `UNVERIFIED` (0.10).
- **Location Relevance (0-1.0)**: Preferred buyer state match (1.0), primary industrial corridor (0.85), secondary (0.70).
- **Data Confidence (0-1.0)**: Provenance confidence index based on statutory backing.

### Package Evaluation & Decision Assessment

The package evaluation computes 4 core indices and evaluates 6 key decision criteria:

1. **Standards Coverage**: Proportion of line items mapped to indexed BIS specifications.
2. **Compliance Coverage**: Proportion of items meeting statutory compliance readiness.
3. **Sourcing Coverage**: Proportion of items with eligible suppliers or sourcing regions.
4. **Verification Coverage**: Proportion of items having verified BIS enterprise manufacturers.
5. **Readiness Score (0-100%)**:
   $$\text{Readiness} = 0.30 \times \text{Standards} + 0.30 \times \text{Compliance} + 0.25 \times \text{Sourcing} + 0.15 \times \text{Verification} - \text{Penalties}$$
6. **Procurement Decision Summary**: Explicitly answers:
   - Are all requested items standards-covered?
   - Are compliant sourcing options available?
   - Which items have strong sourcing coverage?
   - Which items require supplier verification?
   - Which items have insufficient sourcing evidence?
   - Is the overall package procurement-ready?

---

## Phase 3: Evidence & Verification Engine

Phase 3 transforms BharatBuy from sourcing discovery into an explicit, auditable **Evidence & Verification Engine**:

```text
Startup Requirements
         ↓
BIS / Indian Standards Retrieval
         ↓
Eligible Source Discovery
         ↓
Structured Evidence Synthesizer (7 Typed Evidence Records)
         ↓
Decoupled Dual-Score Evaluation:
   ├── Product Suitability Score (0.0 - 1.0)
   └── Source Trust & Provenance Score (0.0 - 1.0)
         ↓
4-State Procurement Decision Engine (READY / READY_WITH_VERIFICATION / INSUFFICIENT_EVIDENCE / NOT_RECOMMENDED)
         ↓
Evidence Drawer UI + Grounded AI Briefing ([SUPPORTED BY EVIDENCE] vs [INFERRED] vs [REQUIRES VERIF])
```

### Critical CML Data Audit & Safety Guarantees
- **No False Confirmation**: A static JSON record in `sourcing-registry-v1.json` is never treated as live proof of active BIS certification.
- **Classification**: Central PSUs with historical CML records are classified as `REQUIRES_LIVE_VERIFICATION` (or `EVIDENCE_AVAILABLE`), industrial corridors as `NOT_APPLICABLE`, and commercial distributors as `NO_EVIDENCE`.
- **Mandatory Portal Audit**: The UI and API explicitly state: *"Verification required on official BIS portal (manakonline.in) before PO release."*

### Decoupled Dual-Score Evaluation Framework
1. **Product Suitability ($S_{\text{suit}}$)**:
   $$S_{\text{suit}} = 0.30 \times \text{Category} + 0.35 \times \text{Standard} + 0.20 \times \text{Compliance} + 0.15 \times \text{Location}$$
   *Strict Zeroing Rule*: If both Category and Standard match are 0.0, $S_{\text{suit}}$ is strictly 0.0 regardless of trust.
2. **Source Trust ($T_{\text{score}}$)**:
   $$T_{\text{score}} = 0.40 \times \text{Identity} + 0.30 \times \text{BIS Evidence} + 0.15 \times \text{Freshness} + 0.15 \times \text{Completeness}$$
   *Trust Levels*: `HIGH` ($\ge 0.80$), `MODERATE` ($0.45 - 0.79$), `LOW` ($< 0.45$).

### 4-State Decision Matrix
- `READY`: $100\%$ sourcing & verification coverage, $\ge 85\%$ readiness, 0 critical blockers.
- `READY_WITH_VERIFICATION`: Recommended sources available; buyer portal check on `manakonline.in` or MTC inspection required.
- `INSUFFICIENT_EVIDENCE`: Sourcing coverage $< 50\%$ or verification coverage $< 30\%$; market survey required.
- `NOT_RECOMMENDED`: Severe mandatory standard failures; re-scoping necessary.

---

## Phase 4: External Verification & Evidence Ingestion Layer

Phase 4 elevates BharatBuy into an active verification and external evidence ingestion platform:

```text
AUTHORITATIVE / EXTERNAL EVIDENCE
               ↓
       EVIDENCE INGESTION
               ↓
       SOURCE VALIDATION
               ↓
       FRESHNESS TRACKING
               ↓
   GUIDED BUYER VERIFICATION WORKFLOW
               ↓
      PROCUREMENT DECISION
```

### Key Capabilities & Invariants
1. **Authoritative Evidence Provider Framework**:
   - `EvidenceProvider` abstract base class with concrete adapters for BIS, Government Gazettes/PSUs, and Commercial Suppliers.
   - `EvidenceProviderRegistry` singleton managing provider dispatching and provenance chains.
2. **Statutory Anti-Bot Compliance & Ethical Integration**:
   - Explicitly rejects CAPTCHA bypasses, scrapers, or circumvention of `manakonline.in` access controls (`can_auto_verify = False`).
   - Provides an interactive 5-point Guided Buyer Verification Workflow directing buyers to the official portal with pre-formatted search queries.
3. **Evidence Freshness & Expiration Tracking**:
   - Strict 4-state lifecycle: `CURRENT`, `AGING`, `STALE`, and `UNKNOWN`.
   - Historical static CML registry records default to `UNKNOWN` and require live verification.
4. **Immutable Verification Audit Trail**:
   - Thread-safe `AuditService` logging verification events (`log_id`, `source_id`, `action`, `previous_status`, `new_status`, `verification_method`, `actor`, `timestamp`, `notes`) with zero secret leaks.
5. **Strict Decision Semantics**:
   - Completely eliminates premature purchase releases ("Immediate PO release permitted"); strictly enforced as *"Procurement-ready for buyer approval"*.

---

## Phase 5: Production Demo & Data Integrity Hardening

### 1. Isolated Demo Mode (`BHARATBUY_DEMO_MODE`)
- Configure in `.env` or `backend/app/core/config.py`:
  - `BHARATBUY_DEMO_MODE=false` (Production Default): Strict zero-fabrication guarantee. Loads only authentic entities from `data/sourcing-registry-v1.json`. All demo records are strictly filtered out.
  - `BHARATBUY_DEMO_MODE=true` (Demo Environment): Loads isolated demonstration entities from `data/demo-sourcing-registry-v1.json` with explicit `DEMO_DATA` provenance labels and `is_demo_data: true`.

### 2. Strict Data Provenance Labels
All sourcing entries carry deterministic provenance:
- `AUTHORITATIVE`: Fully verified institutional manufacturer with laboratory compliance.
- `GOVERNMENT_RECORD`: Central PSU, Ministry Gazette, or statutory public enterprise.
- `BIS_EVIDENCE`: Verified BIS CML license in registry/claims.
- `REGISTRY_EVIDENCE`: General verified sourcing registry entry.
- `BUYER_VERIFIED`: Confirmed on official BIS portal by authenticated buyer audit.
- `SUPPLIER_DECLARATION`: Commercial distributor or unverified supplier.
- `REGION_ONLY`: Industrial corridor cluster without individual vendor CML attached.
- `DEMO_DATA`: Isolated demo entity.

### 3. 5-Metric Package Coverage Grid
- **Standards Coverage %**: Proportion of items mapped to indexed Indian Standards.
- **Compliance Coverage %**: Proportion of items meeting statutory testing parameters.
- **Sourcing Coverage %**: Proportion of items with discovered industrial hubs or manufacturers.
- **Evidence Coverage %**: Proportion of items with authoritative / documented evidence.
- **Verification Coverage %**: Proportion of items with verified manufacturing entities.

### 4. Official Demonstration Guide
- See [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) for a step-by-step 3–5 minute presentation flow and jury evaluation guide across our 3 production presets (`SOLAR PROJECT`, `FACTORY CONSTRUCTION`, `IT / OFFICE PROCUREMENT`).

---

## API Endpoints

- `POST /api/v1/procurement/analyze` (or direct alias `POST /api/procurement/analyze`)
  - Full-package procurement intelligence pipeline with 4-state decisions, trust scores, evidence chains, and demo mode indicator.
- `GET /api/v1/procurement/sources`
  - Query authentic sourcing registry. Filters: `category`, `standard_id`, `verification_status`, `source_type`.
- `GET /api/v1/procurement/sources/{source_id}`
  - Retrieve detailed metadata, BIS licenses, location coordinates, and profile.
- `GET /api/v1/procurement/sources/{source_id}/evidence`
  - Retrieve structured `SourceEvidenceResponse` with trust breakdown, provenance chain, and traceable evidence records.
- `GET /api/v1/procurement/sources/{source_id}/verification`
  - Retrieve official BIS verification workflow instructions, destination URL, 5-point checklist, and audit trail.
- `POST /api/v1/procurement/sources/{source_id}/verify`
  - Record buyer manual verification affirmation with audit log entry and verified status elevation.
- `POST /api/v1/recommend`
  - Single procurement specification query search.
- `GET /api/v1/standards/{standard_id}`
  - Standard item metadata, testing clauses, and connected standards.
- `GET /api/v1/graph/{standard_id}`
  - React Flow knowledge graph nodes and edges.
- `GET /api/v1/health`
  - System status, total standards count (559), active model, and `is_demo_mode`.

---

## Environment Variables

| Variable | Default | Description | Production Guidance |
| :--- | :--- | :--- | :--- |
| `DATABASE_PATH` | `data/standards-database-v5.db` | SQLite database file containing 559 Indian Standards | Keep authoritative read-only path |
| `GRAPH_PATH` | `data/standards-knowledge-graph-v5.json` | Knowledge graph relationships JSON | Keep authoritative read-only path |
| `MODEL_TYPE` | `baseline` | Recommendation engine (`baseline` or `custom`) | Use `baseline` or load team `.pkl` |
| `BHARATBUY_DEMO_MODE` | `false` | Production vs Demo mode toggle | **`false` in production** (excludes demo records) |
| `GEMINI_API_KEY` | `""` (empty) | Google Gemini API key for explainability | Optional. Falls back to deterministic briefing if unset |
| `PORT` | `8000` | Backend API port | `8000` or port assigned by cloud host |
| `HOST` | `0.0.0.0` | Backend network bind host | `0.0.0.0` for container / remote accessibility |
| `CORS_ORIGINS` | `["http://localhost:3000", ...]` | Allowed HTTP origins for CORS | Restrict to production frontend domain |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | Frontend REST API endpoint URL | Set to reverse-proxy or production API URL |

---

## Production Mode vs Demo Mode

- **Production Mode (`BHARATBUY_DEMO_MODE=false`, Default)**:
  - Strict **Zero-Fabrication Guarantee**.
  - Loads exclusively authentic manufacturing enterprises (Central PSUs, Gazette-documented entities) and state industrial development corridors from `data/sourcing-registry-v1.json`.
  - All synthetic demo sources (`SRC-DEMO-*`) are strictly excluded.
  - Sourcing decisions require buyer verification before final approval.

- **Demo Mode (`BHARATBUY_DEMO_MODE=true`)**:
  - Activated explicitly for jury evaluation or offline presentation scenarios.
  - Loads isolated demonstration entities from `data/demo-sourcing-registry-v1.json` carrying the explicit `DEMO_DATA` provenance label.
  - Header displays a visible amber `DEMO MODE ACTIVE` badge.

---

## Testing & Quality Assurance

The repository includes a comprehensive, automated test suite (**78 automated tests** passing in ~2 seconds):

```powershell
# Run full backend test suite:
backend\.venv\Scripts\python.exe -m pytest backend/tests/ -v

# Run frontend production build:
cd frontend
npm run build
```

Test coverage includes:
- Hybrid BM25 + semantic vector retrieval
- Specification unit and voltage normalization
- Item-level and package-level statutory compliance
- Decoupled scoring ($S_{\text{suit}}$ suitability vs $T_{\text{score}}$ trust)
- 4-state human-governed procurement decision engine
- External evidence provider abstractions & provenance labeling
- Anti-bot compliance & guided buyer verification workflow
- Freshness state tracking (`CURRENT`, `AGING`, `STALE`, `UNKNOWN`)
- Thread-safe audit trail logging
- End-to-end multi-category smoke test (Cables, TMT Steel, Solar PV Modules)
- Negative input handling and error sanitation

---

## Deployment & Docker Instructions

### 1. Docker Compose (Full Stack)

To run BharatBuy in isolated containers:

```bash
# Build and launch both backend and frontend:
docker compose up --build -d

# Verify running containers:
docker compose ps

# View backend logs:
docker compose logs -f backend
```

- **Frontend**: Available at `http://localhost:3000`
- **Backend API**: Available at `http://localhost:8000/api/v1`
- **Swagger Documentation**: `http://localhost:8000/api/v1/docs`

### 2. Standalone Container Builds

```bash
# Build backend image from repository root context:
docker build -t bharatbuy-backend:latest -f backend/Dockerfile .

# Build frontend image:
docker build -t bharatbuy-frontend:latest --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1 frontend/
```

### 3. Production Deployment Notes
- When deploying to production infrastructure (e.g. AWS ECS, GCP Cloud Run, or Azure App Service):
  - Set `BHARATBUY_DEMO_MODE=false`.
  - Pass the production API URL into `NEXT_PUBLIC_API_URL` during frontend build.
  - Configure `CORS_ORIGINS` to accept only the production frontend origin.
  - Volume mount `data/` as read-only.

---

## Real-World Evidence Disclaimer

> **Statutory Notice**: BharatBuy provides evidence-backed procurement intelligence. Certification validity and supplier eligibility should be independently verified before buyer approval.

---

## System Limitations & Ethical Integration

1. **Statutory BIS Portal Protection**:
   - The official Bureau of Indian Standards portal (`manakonline.in`) implements CAPTCHA challenges and anti-bot protections.
   - BharatBuy strictly respects statutory cybersecurity controls: it **never scrapes, automates, or bypasses** official BIS portal controls.
   - Instead, BharatBuy provides a structured, 5-point **Guided Buyer Verification Workflow** directing procurement officers to the authoritative government portal.

2. **Offline Registry Scope**:
   - Primary standards retrieval queries the local SQLite database of **559 Indian Standards**.
   - Sourcing recommendations are drawn from authentic state industrial corridors and documented Central PSUs.
   - Dynamic market availability and volatile commodity pricing require direct supplier quotations.

3. **Grounded Explainability**:
   - If a Gemini API key is not supplied or the API is unreachable, BharatBuy automatically emits a deterministic, grounded briefing backed directly by retrieved standards and registered source evidence. No hallucinations are possible.


