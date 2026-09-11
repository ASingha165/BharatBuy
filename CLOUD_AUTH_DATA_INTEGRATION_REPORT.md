# BHARATBUY — CLOUD AUTH, NEON DATA MIGRATION & UI CLEANUP REPORT
**Date**: September 10, 2026  
**Project**: SIH26108 — BharatBuy AI Procurement Intelligence  
**Environment**: Production Ready (FastAPI + Neon PostgreSQL + Next.js + Firebase Authentication)

---

## 1. Executive Summary & Architecture Status

BharatBuy has transitioned from a local-only prototype into a **device-independent, cloud-native procurement intelligence engine**. All persistent application data now lives in an enterprise-grade cloud database (Neon PostgreSQL in AWS Asia Pacific Singapore), authenticated via **Firebase Authentication** on both client and server, while retaining the Stitch design system, API contracts, and an offline SQLite fallback.

```text
                                  CLIENT
                   Next.js 14 Web Application (:3000)
                     ├── Stitch Design System (Pure CSS Tokens)
                     ├── Clean Initial Form State (Empty Inputs)
                     ├── Industrial Domain Presets (Solar, Factory, IT)
                     └── Firebase Web SDK (Email/Password Auth)
                                    │
                         HTTPS / Authorization: Bearer <idToken>
                                    ▼
                                 BACKEND
                          FastAPI API Engine (:8000)
                     ├── Firebase Admin SDK Token Verification (RS256)
                     ├── Account Linking & Auto-Upsert via UID
                     ├── Hybrid Retrieval (BM25 + Semantic Vectors)
                     └── Grounded AI Explainability Layer
                                    │
                                    ▼
                             DATA PERSISTENCE
                  Dual-Engine Database Manager (Mode B: Active)
                     ├── Neon PostgreSQL (Cloud Production DB)
                     │     ├── standards (559 rows, Checksum: 26068468...)
                     │     ├── users (with firebase_uid column)
                     │     └── sourcing_sources (17 authentic entities)
                     └── SQLite Fallback (Local Development & Airgap)
```

---

## 2. Firebase Authentication Integration & Security Guardrails

### 2.1 Architecture & Token Verification Flow
- **Client Authentication**: Implemented via `@firebase/auth` within `frontend/lib/auth-context.tsx`. Users sign up or sign in using their work email and password.
- **Client Credentials**: Sourced securely from `process.env.NEXT_PUBLIC_FIREBASE_*` with fallback defaults in `frontend/lib/firebase.ts`.
- **Token Transmission**: Upon authentication, the client obtains a cryptographically signed Firebase ID token via `getIdToken()` and attaches it to the `Authorization: Bearer <idToken>` header.
- **Server-Side Cryptographic Verification**: Handled by `backend/app/core/firebase.py` and `backend/app/services/auth_service.py` using `firebase-admin` (RS256 certificate verification). The backend **never trusts** client-submitted claims, UIDs, or emails.
- **Profile Synchronization**: `POST /api/v1/auth/firebase-sync` automatically links verified Firebase UIDs to existing accounts by email or provisions a new user record.
- **Backward Compatibility**: Requests signed with legacy HMAC-SHA256 JWT tokens continue to be supported seamlessly during transition.

### 2.2 Security Compliance
| Security Check | Implementation | Status |
| :--- | :--- | :---: |
| **No Client-Supplied UID Trust** | Backend extracts UID only from cryptographically validated token payload | **PASS** |
| **Zero Secret Leakage** | No Firebase service account private keys or database passwords in source/logs | **PASS** |
| **Dual Token Algorithm Guard** | Local HS256 tokens and Firebase RS256 tokens segregated without false network roundtrips | **PASS** |
| **Session Isolation** | Test clients and browser sessions maintain isolated auth contexts | **PASS** |

---

## 3. Neon PostgreSQL Production Migration & Parity Verification

### 3.1 Migration Execution & Parity Verification
Executed via `backend/scripts/migrate_sqlite_to_postgres.py` against Neon PostgreSQL (`AWS Asia Pacific 1 - Singapore`):

| Data Domain | Source (SQLite / JSON) | Neon PostgreSQL | Parity Status | Verification Metric |
| :--- | :---: | :---: | :---: | :--- |
| **Standards Catalog** | 559 rows | 559 rows | **PASS** | MD5: `26068468cb17d05f4d61b5aa07f96fac` |
| **Registered Users** | 1 row | 1 row | **PASS** | Identity & password_hash parity |
| **Sourcing Sources** | 17 entities | 17 entities | **PASS** | 10 corridors + 7 documented PSUs/labs |
| **Demo Data Isolation** | 3 demo records | 0 records | **PASS** | 0 demo entities in production DB |

### 3.2 Dual-Database Engine Switch
- **Mode B (Production Cloud)**: Active when `DATABASE_URL` is configured.
- **Mode A (Local Airgap Fallback)**: Automatically active when `DATABASE_URL` is unset or blank, preserving uninterrupted offline development and demonstration capabilities.

---

## 4. UI Cleanliness & Initial State Audit

### 4.1 Form Initialization Cleanliness
`frontend/components/ProcurementAnalysisForm.tsx` has been updated to initialize strictly with empty values:
- **Buyer / Startup Entity Name**: Initialized to `""` (placeholder prompt: `e.g. Bharat Infrastructure & Power Corp`).
- **Procurement Line Items**: Initialized to a single empty row:
  - Item name: `""`
  - Quantity: `1`
  - Unit: `""`
  - Technical specifications: `""`
- **Natural Language Input**: Initialized to `""`.
- **Results View**: Completely hidden until the user explicitly executes an analysis.

### 4.2 Presets Retained for Evaluators & Demos
The industrial domain scenario buttons remain readily accessible to evaluators:
1. **SOLAR PROJECT**: 500 kW rooftop solar plant (solar PV modules, grid-tie inverter, DC solar cables, mounting structures).
2. **FACTORY CONSTRUCTION**: Industrial facility expansion (TMT steel rebar Fe 500D, Portland Pozzolana Cement, structural steel channels).
3. **IT / OFFICE PROCUREMENT**: Corporate data & workspace procurement (UPS units, Cat6 Ethernet cabling).

---

## 5. File & Dependency Classification Inventory

All files across the repository have been inspected and classified:

### 5.1 Authoritative Production Data
- `data/standards-database-v5.db`: Local SQLite master database (559 BIS standards).
- `data/standards-knowledge-graph-v5.json`: Inter-standard dependency and normative reference graph.
- `data/sourcing-registry-v1.json`: Authentic Indian sourcing registry (17 authentic records).
- `data/demo-sourcing-registry-v1.json`: Isolated demo registry (3 demo entities, never in production DB).

### 5.2 Application Backend Modules
- `backend/app/main.py`: FastAPI entrypoint, lifespan handlers, CORS middleware.
- `backend/app/core/config.py`: Central Pydantic settings with dual-database and Firebase settings.
- `backend/app/core/database.py`: Dual-engine database connection manager (PostgreSQL / SQLite).
- `backend/app/core/firebase.py`: Firebase Admin SDK token verification helper.
- `backend/app/models/auth.py`: Pydantic validation schemas for authentication and profile sync.
- `backend/app/services/auth_service.py`: Authentication business logic, token verification, profile upsert.
- `backend/app/repositories/user_repository.py`: Multi-dialect SQL repository for user profiles.
- `backend/app/repositories/standards_repository.py`: Standards catalog repository.
- `backend/app/repositories/sourcing_repository.py`: Sourcing registry repository.
- `backend/app/api/routes/auth.py`: `/signup`, `/signin`, `/signout`, `/firebase-sync`, `/me`.
- `backend/scripts/migrate_sqlite_to_postgres.py`: Automated migration and verification script.

### 5.3 Application Frontend Modules
- `frontend/lib/firebase.ts`: Firebase Web SDK initialization with SSR safety.
- `frontend/lib/auth-context.tsx`: Context provider listening to Firebase auth state and syncing with backend.
- `frontend/lib/api.ts`: Centralized Axios client with automatic Bearer token propagation.
- `frontend/app/signin/page.tsx`: Sign-in screen using Stitch design tokens with clean empty inputs.
- `frontend/app/signup/page.tsx`: Registration screen with statutory procurement consent.
- `frontend/components/ProcurementAnalysisForm.tsx`: Clean-slate procurement analysis form.
- `frontend/components/SourcingMap.tsx`: SSR-safe Leaflet sourcing visualization.

---

## 6. Verification & Automated Test Suite Results

### 6.1 Backend Pytest Suite: 114/114 Tests Passing (100%)
Ran full pytest test suite against active cloud database:
```powershell
& "d:\BharatBuy\backend\.venv\Scripts\python.exe" -m pytest backend/tests/ -q
```
**Result**:
```text
114 passed, 7 warnings in 227.35s (0:03:47)
```
**Breakdown across 16 Test Modules**:
1. `backend/tests/test_firebase_auth.py`: **7/7 PASSED** (token verification, sync, profile upsert, linking, 401 guard)
2. `backend/tests/test_auth.py`: **9/9 PASSED** (signup, signin, cookie sessions, password hashing, signout)
3. `backend/tests/test_database_switch.py`: **3/3 PASSED** (dual-database manager switching, parity, fallback)
4. `backend/tests/test_health.py`: **1/1 PASSED** (health check status & metadata)
5. `backend/tests/test_normalizer.py`: **4/4 PASSED** (query normalization, units, voltages)
6. `backend/tests/test_model_pipeline.py`: **3/3 PASSED** (baseline recommendation pipeline)
7. `backend/tests/test_recommendations.py`: **2/2 PASSED** (ranking, top_k, scoring)
8. `backend/tests/test_graph.py`: **1/1 PASSED** (knowledge graph queries)
9. `backend/tests/test_procurement_pipeline.py`: **22/22 PASSED** (retrieval, package evaluation, compliance)
10. `backend/tests/test_sourcing_intelligence.py`: **13/13 PASSED** (deterministic scoring, corridors, PSUs)
11. `backend/tests/test_evidence_engine.py`: **14/14 PASSED** (decoupled dual scoring, claim trace, 4-state decisions)
12. `backend/tests/test_phase4_verification.py`: **8/8 PASSED** (external provider abstraction, audit logging)
13. `backend/tests/test_phase5_hardening.py`: **11/11 PASSED** (demo isolation, 5-metric coverage, AI fallback)
14. `backend/tests/test_phase6_production_validation.py`: **10/10 PASSED** (negative inputs, edge cases, contracts)
15. `backend/tests/test_verification_semantics.py`: **4/4 PASSED** (buyer governance language, PO release guards)
16. `backend/tests/test_10_scenarios.py`: **2/2 PASSED** (end-to-end multi-category procurement workflows)

### 6.2 Next.js Production Build: 100% Clean
Ran production build:
```powershell
cd frontend && npm run build
```
**Result**:
```text
 ✓ Compiled successfully
   Linting and checking validity of types ...
   Collecting page data ...
 ✓ Generating static pages (6/6) 
   Finalizing page optimization ...
   Collecting build traces ...

Route (app)                              Size     First Load JS
┌ ○ /                                    83.6 kB         230 kB
├ ○ /_not-found                          882 B          85.3 kB
├ ○ /signin                              4.82 kB         158 kB
└ ○ /signup                              5.43 kB         158 kB
+ First Load JS shared by all            84.4 kB
```

---

## 7. Production Readiness Scorecard

| Criteria | Target | Actual | Verification | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Authentication** | Firebase Auth + Admin Verification | Integrated client & backend | `test_firebase_auth.py` (7/7) | **READY** |
| **Production Database** | Cloud PostgreSQL (Neon) | 559 standards, 17 sources | Parity checksum: `26068468...` | **READY** |
| **Offline Fallback** | SQLite v5 database intact | Auto-fallback when URL empty | `test_database_switch.py` (3/3) | **READY** |
| **Initial UI State** | Completely empty inputs | Buyer & line items blank | Checked `ProcurementAnalysisForm` | **READY** |
| **Preset Scenarios** | 3 industrial scenarios | Click-to-load preserved | Tested presets | **READY** |
| **Stitch Visuals** | Unaltered design system | Pure CSS design tokens | `npm run build` (0 errors) | **READY** |
| **Zero Secret Leaks** | No passwords/keys in code | `.env.example` clean | Audit completed | **READY** |
| **Backend Test Suite** | 100% pass rate | 114/114 passing | pytest run: 114 passed | **READY** |
| **Frontend Production Build** | Zero compile errors | 6/6 static routes built | Next.js 14 build verified | **READY** |
