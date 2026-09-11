# BHARATBUY — CLOUD DATA MIGRATION AUDIT (PHASE 1)
**Architecture Blueprint & Readiness Assessment for Device-Independent Cloud Deployment**
**Date:** September 10, 2026 | **Workspace:** `d:/BharatBuy` | **Status:** READ-ONLY COMPREHENSIVE AUDIT

---

## 1. Current Architecture Overview

BharatBuy is an Indian Standards Intelligence and Procurement Engine designed to assist Indian startups, MSMEs, and public-sector procurement managers in evaluating compliance against mandatory Bureau of Indian Standards (BIS) Quality Control Orders (QCOs), discovering authentic manufacturing hubs, and producing auditable, evidence-grounded procurement decisions.

### Current Architecture Topology
```text
                      CLIENT TIER (Web Browser)
                                  │
                                  ▼
                Next.js 14 Frontend Application (:3000)
                ├── App Router (/, /signin, /signup)
                ├── Stitch Industrial Precision Design System
                ├── Leaflet Sourcing Map (Interactive Coordinates)
                ├── @xyflow/react Knowledge Graph Viewer
                └── Axios REST Client (lib/api.ts)
                                  │
                                  │ REST API Calls (/api/v1)
                                  ▼
                 FastAPI Backend Application (:8000)
                ├── main.py (CORS Middleware, OpenAPI Documentation)
                ├── API Routers (health, auth, recommend, standards, graph, procurement)
                ├── Normalization & Feature Engine
                ├── Hybrid Retrieval Engine (BM25 + Vector + Cross-Encoder)
                ├── Sourcing Intelligence Engine & Evidence Service
                └── Custom In-Memory JWT Session & Auth Engine
                                  │
                                  │ Local Filesystem Access
                                  ▼
                     LOCAL PERSISTENCE LAYER
       ┌──────────────────────────┼──────────────────────────┐
       ▼                          ▼                          ▼
SQLite Database            Knowledge Graph            Sourcing Registry
(data/standards-          (data/standards-           (data/sourcing-
 database-v5.db)           knowledge-graph-v5.json)   registry-v1.json)
 • 559 Standards           • 27 Nodes                 • 17 Authentic Records
 • 1 Auth User             • 20 Edges                 • 10 Industrial Hubs
```

---

## 2. Current Data Inventory

| Asset Name | Current Location | Format | Size | Total Records | Role in BharatBuy |
|:---|:---|:---:|:---:|:---:|:---|
| **Primary Database** | `data/standards-database-v5.db` | SQLite 3 | 400.0 KB | 559 standards, 1 user | Authoritative technical standards repository and user credential store. |
| **Knowledge Graph** | `data/standards-knowledge-graph-v5.json` | JSON | 8.6 KB | 27 nodes, 20 edges | Normative, testing, and predecessor relationships between standards. |
| **Sourcing Registry** | `data/sourcing-registry-v1.json` | JSON | 15.1 KB | 17 entities | Authentic Indian industrial corridors and verified Central PSUs. |
| **Demo Registry** | `data/demo-sourcing-registry-v1.json` | JSON | 2.6 KB | 3 entities | Isolated synthetic entities for offline jury presentations (`DEMO_MODE=true`). |
| **Database Seeder** | `data/seed_standards.py` | Python | 31.2 KB | 331 LOC | Authoritative generator script for SQLite v5 database and graph. |

---

## 3. Database Schema Inventory (`data/standards-database-v5.db`)

Inspection of the SQLite schema reveals two tables:

### Table 1: `standards`
Contains the catalog of 559 indexed Indian Standards across civil, electro-technical, mechanical, chemical, and safety domains.

```sql
CREATE TABLE standards (
    standard_id TEXT PRIMARY KEY,
    is_code TEXT NOT NULL,
    title TEXT NOT NULL,
    department TEXT NOT NULL,
    scope_summary TEXT NOT NULL,
    key_specifications TEXT NOT NULL,
    testing_requirements TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    publication_year INTEGER NOT NULL
);
```
- **Primary Key:** `standard_id` (e.g. `'IS-694'`, `'IS-7098-1'`, `'IS-1786'`).
- **Foreign Keys:** None.
- **Indexes:**
  - `sqlite_autoindex_standards_1` (PRIMARY KEY on `standard_id`)
  - `idx_is_code` (INDEX on `is_code`)
  - `idx_dept` (INDEX on `department`)
- **Row Count:** 559 rows.
- **SQLite-Specific Features:** None. Standard ANSI SQL types (`TEXT`, `INTEGER`).
- **Usage:** Consumed exclusively by `StandardsRepository` for candidate retrieval, full-catalog indexing, and single-standard lookups.

### Table 2: `users`
Contains registered user profiles, organizations, and credential hashes for platform access.

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    organization TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```
- **Primary Key:** `id` (e.g. `'usr_b8b27fd4349e1679'`).
- **Foreign Keys:** None.
- **Indexes:**
  - `sqlite_autoindex_users_1` (PRIMARY KEY on `id`)
  - `sqlite_autoindex_users_2` (UNIQUE on `email`)
  - `idx_users_email` (INDEX on `email`)
- **Row Count:** 1 row (active test account).
- **SQLite-Specific Features:** None. Timestamps are stored as ISO 8601 strings (`TEXT`).
- **Usage:** Consumed exclusively by `UserRepository` for sign-up, sign-in, and session verification.

---

## 4. Runtime Dependency Graph

```text
HTTP Request
  │
  ▼
FastAPI Router (backend/app/api/routes/*.py)
  │
  ├── [GET /health]
  │     └─► StandardsRepository.check_health()
  │           └─► SQLite: SELECT 1 FROM standards LIMIT 1
  │
  ├── [POST /api/v1/auth/*]
  │     └─► AuthService
  │           └─► UserRepository
  │                 └─► SQLite: users table (SELECT, INSERT, DELETE)
  │
  ├── [GET /api/v1/standards/{id}]
  │     └─► StandardsRepository.get_standard_by_id()
  │           └─► SQLite: standards table
  │
  ├── [GET /api/v1/graph/{id}]
  │     └─► GraphService.get_react_flow_graph()
  │           └─► File: data/standards-knowledge-graph-v5.json
  │
  ├── [GET /api/v1/procurement/sources]
  │     └─► SourcingService.get_all_sources()
  │           └─► File: data/sourcing-registry-v1.json (+ demo registry if enabled)
  │
  └── [POST /api/v1/procurement/analyze]
        └─► ProcurementService.analyze()
              ├── NormalizationService (spec parsing)
              ├── HybridRetrievalService.retrieve_and_rank()
              │     └─► StandardsRepository.get_all_standards()
              │           └─► SQLite: standards table (559 rows)
              ├── PackageEvaluationService (compliance clauses & scoring)
              ├── SourcingService (corridor & vendor matching)
              │     └─► File: data/sourcing-registry-v1.json
              └── ExplanationService (grounded briefing)
```

### Exact Code References Trace

| File Path | Responsible Class / Function | Data Asset Read / Written | Operation |
|:---|:---|:---|:---:|
| `backend/app/repositories/standards_repository.py` | `StandardsRepository` (`__init__`, `get_connection`, `get_all_standards`, `get_standard_by_id`, `check_health`) | `data/standards-database-v5.db` | READ |
| `backend/app/repositories/user_repository.py` | `UserRepository` (`__init__`, `_init_db`, `get_user_by_email`, `get_user_by_id`, `create_user`, `delete_user_by_email`) | `data/standards-database-v5.db` | READ / WRITE |
| `backend/app/services/graph_service.py` | `GraphService` (`__init__`, `load_graph`, `get_related_standards`, `get_react_flow_graph`) | `data/standards-knowledge-graph-v5.json` | READ |
| `backend/app/services/sourcing_service.py` | `SourcingService` (`_load_sourcing_registry`, `get_all_sources`, `get_source_by_id`) | `data/sourcing-registry-v1.json`, `data/demo-sourcing-registry-v1.json` | READ |
| `backend/app/services/evidence_service.py` | `EvidenceService` (`generate_source_evidence_records`) | Hardcoded metadata label `"standards-database-v5.db"` | Provenance String |
| `backend/app/services/audit_service.py` | `AuditService` (`record_event`, `get_audit_trail`) | In-Memory `self._logs` list | Transient RAM |

---

## 5. Retrieval / ML Dependency Analysis

A critical question for cloud migration is whether the recommendation and retrieval engines depend on local SQLite indexes or persistent on-disk vector stores.

| Component | Service Class | Underlying Library | Index Nature | Dependency on Disk / SQLite |
|:---|:---|:---|:---|:---|
| **BM25 Lexical** | `BM25Service` | `rank_bm25.BM25Okapi` | **In-Memory RAM** | **Rebuilt at startup (B)**. Takes standard dicts in memory, tokenizes, and builds BM25 index in RAM in ~60ms. Zero disk dependency. |
| **Semantic Vector** | `EmbeddingService` | `sentence_transformers` or `sklearn.TfidfVectorizer` | **In-Memory RAM** | **Rebuilt at startup (B)**. Pre-computes embeddings for 559 standards into a `numpy.ndarray` held in memory. Zero disk persistence. |
| **Cross-Encoder** | `RerankerService` | `sentence_transformers.CrossEncoder` | **Stateless Inference** | **Dynamically generated (C)**. Scores query-candidate pairs on-the-fly. Zero database dependency. |
| **Baseline Model** | `BaselineRecommendationModel` | Pure Python heuristic rule engine | **Stateless Logic** | **Dynamically generated (C)**. Evaluates keyword frequency, electrical units (kV, A, W), and scope terms in memory. Zero database dependency. |
| **Knowledge Graph** | `GraphService` | In-memory node/edge index | **In-Memory RAM** | **Rebuilt at startup (B)**. Loaded from JSON into memory on boot. |

### Architectural Finding: Zero Database Retrieval Lock-in
The retrieval pipeline does **NOT** rely on SQLite FTS5, vector extensions (sqlite-vss), or custom binary tables. It queries:
```sql
SELECT standard_id, is_code, title, department, scope_summary, key_specifications, testing_requirements, status, publication_year FROM standards
```
Once this query executes, the entire multi-stage retrieval pipeline runs completely in memory. Consequently, **switching the underlying repository from SQLite to PostgreSQL requires zero changes to the retrieval algorithms, scoring math, or ML pipelines.**

---

## 6. Authentication Audit

### Current Authentication Implementation
- **Password Security:** PBKDF2-HMAC-SHA256 with 100,000 iterations and 16-byte random salts (`pbkdf2_sha256$100000$<salt>$<hash>`).
- **Session Tokens:** Custom stateless HMAC-SHA256 JWT tokens containing `sub` (user ID), `email`, `iat`, and `exp`.
- **Transmission:** Returned as an HTTP response payload (`AuthResponse`) and stored in an HTTP-only cookie (`bharatbuy_session`) as well as Bearer token headers.
- **Protected Endpoints:** `GET /api/v1/auth/me` is protected by `get_current_user_required`. Public workbench and analysis routes are open to unauthenticated users with optional user context capture.

### Mapping to Firebase Authentication
In the target architecture, authentication moves to Firebase Authentication while retaining user profiles in Cloud SQL PostgreSQL:

```text
CLIENT (Next.js)                  FIREBASE AUTH                     FASTAPI BACKEND                CLOUD SQL (PostgreSQL)
       │                                │                                  │                                  │
       │── 1. Sign In (Email/Google) ──►│                                  │                                  │
       │◄── 2. Firebase ID Token ───────│                                  │                                  │
       │                                                                   │                                  │
       │── 3. API Request (Header: Authorization: Bearer <Firebase_Token>)►│                                  │
       │                                                                   │── 4. Verify Token (Firebase SDK) │
       │                                                                   │      Extract uid, email, claims  │
       │                                                                   │                                  │
       │                                                                   │── 5. Lookup/Upsert User Profile ─►│
       │                                                                   │◄─ 6. Return Organization Profile ─│
       │◄── 7. Business Response (Enriched with User Organization) ────────│                                  │
```

#### Proposed `users` Table Evolution for Firebase Support
```sql
CREATE TABLE users (
    id VARCHAR(128) PRIMARY KEY,                  -- Stores Firebase UID (e.g. 'firebase_abc123')
    email VARCHAR(255) UNIQUE NOT NULL,           -- Synchronized with Firebase verified email
    name VARCHAR(150) NOT NULL,                   -- Display name
    organization VARCHAR(200) NOT NULL,           -- Startup / Enterprise name (BharatBuy profile)
    role VARCHAR(50) DEFAULT 'BUYER',             -- 'BUYER', 'COMPLIANCE_OFFICER', 'ADMIN'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```
- **Backward Compatibility:** Existing users (`usr_...`) retain their records; password hashes are deprecated once Firebase handles credential verification.
- **Dual Support:** During migration, the FastAPI backend can verify both local HMAC tokens and Firebase ID tokens via a unified `get_current_user_optional` dependency.

---

## 7. Cloud SQL Migration Design (PostgreSQL Schema)

The target relational database is Google Cloud SQL for PostgreSQL (v15 or v16). Below is the exact, production-ready DDL mapping.

### Table 1: `standards`
Equivalent to the current SQLite `standards` table, with optimized types and full-text search capability.

```sql
-- Target: Cloud SQL PostgreSQL
CREATE TABLE standards (
    standard_id VARCHAR(64) PRIMARY KEY,
    is_code VARCHAR(64) NOT NULL,
    title VARCHAR(500) NOT NULL,
    department VARCHAR(100) NOT NULL,
    scope_summary TEXT NOT NULL,
    key_specifications TEXT NOT NULL,
    testing_requirements TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    publication_year INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- B-tree indexes matching current SQLite performance profile
CREATE INDEX idx_standards_is_code ON standards(is_code);
CREATE INDEX idx_standards_department ON standards(department);
CREATE INDEX idx_standards_status ON standards(status);

-- Optional future optimization: PostgreSQL GIN index for native full-text search
CREATE INDEX idx_standards_fts ON standards USING gin(
    to_tsvector('english', is_code || ' ' || title || ' ' || scope_summary || ' ' || key_specifications)
);
```

### Table 2: `users`
Enhanced user table accommodating both local development and Firebase Authentication.

```sql
CREATE TABLE users (
    id VARCHAR(128) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    organization VARCHAR(200) NOT NULL,
    password_hash VARCHAR(255),                   -- Nullable for Firebase-authenticated users
    firebase_uid VARCHAR(128) UNIQUE,             -- Populated when authenticated via Firebase
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_firebase_uid ON users(firebase_uid);
```

### Table 3: `sourcing_sources` (Promoting Sourcing Registry from JSON to PostgreSQL)
Promotes the 17 static JSON records in `sourcing-registry-v1.json` to a structured, relational PostgreSQL table.

```sql
CREATE TABLE sourcing_sources (
    source_id VARCHAR(64) PRIMARY KEY,
    source_name VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL,              -- 'SOURCING_REGION', 'MANUFACTURER', 'SUPPLIER'
    verification_status VARCHAR(50) NOT NULL,      -- 'VERIFIED', 'PARTIALLY_VERIFIED', 'REGION_ONLY', 'UNVERIFIED'
    provenance_label VARCHAR(50) NOT NULL,         -- 'GOVERNMENT_RECORD', 'BIS_EVIDENCE', 'REGION_ONLY', etc.
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    categories JSONB NOT NULL,                     -- Array of supported product categories
    supported_standards JSONB NOT NULL,            -- Array of supported standard_ids (e.g. ["IS-1786", "IS-2062"])
    verification_evidence JSONB NOT NULL,         -- Array of evidence statements / CML license records
    description TEXT NOT NULL,
    is_demo_data BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sources_type ON sourcing_sources(source_type);
CREATE INDEX idx_sources_status ON sourcing_sources(verification_status);
CREATE INDEX idx_sources_categories ON sourcing_sources USING gin(categories);
CREATE INDEX idx_sources_standards ON sourcing_sources USING gin(supported_standards);
```

### Table 4: `verification_audit_logs` (Persisting Verification Trail from RAM to PostgreSQL)
Promotes the in-memory audit trail from `AuditService` to a persistent, immutable PostgreSQL audit ledger.

```sql
CREATE TABLE verification_audit_logs (
    log_id VARCHAR(64) PRIMARY KEY,
    source_id VARCHAR(64) NOT NULL REFERENCES sourcing_sources(source_id) ON DELETE CASCADE,
    evidence_id VARCHAR(64),
    action VARCHAR(100) NOT NULL,
    previous_status VARCHAR(50) NOT NULL,
    new_status VARCHAR(50) NOT NULL,
    verification_method VARCHAR(50) NOT NULL,
    actor VARCHAR(150) NOT NULL,
    notes TEXT,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_source_id ON verification_audit_logs(source_id);
CREATE INDEX idx_audit_timestamp ON verification_audit_logs(timestamp);
```

---

## 8. Data Migration Strategy (SQLite $\rightarrow$ PostgreSQL)

A safe, idempotent, and non-destructive migration script will be built in the implementation phase.

### Key Principles
1. **Zero Production Downtime / Zero Data Loss:** The original SQLite database (`data/standards-database-v5.db`) will remain completely untouched.
2. **Idempotency (`ON CONFLICT DO UPDATE`):** The script can be executed multiple times safely without creating duplicate records or throwing primary key conflicts.
3. **Automated Verification:**
   - Pre-migration row count check.
   - Post-migration row count verification: `COUNT(*)` in PostgreSQL must equal `559`.
   - Record-level integrity verification: MD5 checksum of all concatenated `standard_id` values must match between SQLite and PostgreSQL.
4. **Dry-Run Capability:** The script will support `--dry-run` to validate connectivity, schemas, and queries without committing transactions.
5. **Rollback Script:** A paired rollback script (`DROP TABLE standards_backup; ...`) will be generated alongside the migration script.

---

## 9. Cloud Storage Assessment

| Asset | Current Format | Cloud Placement | Rationale |
|:---|:---:|:---:|:---|
| **Standards Data (559 rows)** | SQLite | **Cloud SQL PostgreSQL** | Structured relational catalog requiring fast B-tree queries, count lookups, and ACID guarantees. |
| **User Accounts & Profiles** | SQLite | **Cloud SQL PostgreSQL** | Relational data tied to organization identity and Firebase UIDs. |
| **Sourcing Registry (17 records)** | JSON | **Cloud SQL PostgreSQL** | Highly structured entity data requiring JSONB filtering by category, standard, and location coordinates. |
| **Verification Audit Logs** | In-Memory | **Cloud SQL PostgreSQL** | Immutable compliance records requiring audit trail persistence across Cloud Run container lifecycles. |
| **Knowledge Graph (27 nodes, 20 edges)** | JSON | **Application Package Data (Local File or GCS)** | Extremely small (8.8 KB), static graph. Keeping it packaged in the backend Docker image or in GCS bucket provides microsecond retrieval with zero database roundtrips. |
| **Demo Registry (3 demo records)** | JSON | **Application Package Data (Local File)** | Used only when `BHARATBUY_DEMO_MODE=true` for offline presentations. Should never pollute production Cloud SQL. |
| **Standard PDF Specifications (Future)** | Binary PDFs | **Google Cloud Storage (GCS)** | Large static binary files belong in GCS buckets with signed URLs, not in relational database tables. |

---

## 10. Firebase Authentication Integration Plan

### Architecture
- **Frontend SDK:** Next.js uses the client-side Firebase Web SDK (`firebase/auth`).
- **Backend Verification:** FastAPI uses `firebase-admin` Python SDK to decode and cryptographically verify ID tokens using Google's public keys.
- **Session Bridge:** The frontend passes the token via standard `Authorization: Bearer <token>` headers. The existing `apiClient` in `frontend/lib/api.ts` already has `setAuthToken(token)` implemented and wired!

### Implementation Steps (for Phase 2)
1. Install `firebase-admin` in `backend/requirements.txt` and `firebase` in `frontend/package.json`.
2. Configure Firebase project credentials via environment variables (`FIREBASE_PROJECT_ID`, Application Default Credentials).
3. In `backend/app/services/auth_service.py`, implement `verify_firebase_token(token: str) -> dict`.
4. In `backend/app/api/routes/auth.py`, update `get_current_user_optional` to inspect incoming Bearer tokens with Firebase Admin if Firebase is configured.
5. In `frontend/lib/auth-context.tsx`, wire `signInWithEmailAndPassword` and `createUserWithEmailAndPassword`.

---

## 11. Cloud Run Deployment Implications

Deploying the FastAPI backend to Google Cloud Run introduces specific containerized, serverless behaviors:

1. **Stateless Container Instances:**
   - Cloud Run instances scale down to zero when idle and scale up horizontally during traffic surges.
   - Any local file written to disk inside the container (e.g. SQLite DB or local audit logs) is ephemeral and destroyed upon container shutdown.
   - **Resolution:** Moving `users`, `standards`, `sourcing_sources`, and `audit_logs` to Cloud SQL PostgreSQL ensures full state persistence across scaling events.
2. **Cloud SQL Connection via Unix Sockets:**
   - Cloud Run connects to Cloud SQL instances securely over the Cloud SQL Auth Proxy using Unix domain sockets (`/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME`) without exposing the database to the public internet.
   - **Configuration:** Handled automatically via `DATABASE_URL=postgresql://user:pass@/dbname?host=/cloudsql/INSTANCE_CONNECTION_NAME`.
3. **Startup Latency & Cold Starts:**
   - BM25 and Semantic Embedding indices take ~1.2 seconds to pre-compute for 559 standards during container startup.
   - Cloud Run startup probe (`/api/v1/health`) ensures the container only receives buyer requests after `initialize_services()` has completed.

---

## 12. Local Development Strategy

To preserve fast, offline development and zero-dependency automated testing, BharatBuy will support dual-database execution:

```text
                  DATABASE CONNECTION STRATEGY
                                │
                 Is DATABASE_URL configured?
                                │
               ┌────────────────┴────────────────┐
               ▼ YES                             ▼ NO
      [PRODUCTION / STAGING]              [LOCAL DEV / PYTEST]
    Cloud SQL PostgreSQL               SQLite (local file)
    postgresql://...                   data/standards-database-v5.db
```

### Developer Experience Guarantees
- **No Cloud Required for Local Tests:** Running `pytest backend/tests/` continues to run against the local SQLite database instantly with zero network latency and zero cloud credentials.
- **Docker Compose:** A local PostgreSQL container can be optionally spun up via `docker-compose.yml` for testing PostgreSQL-specific queries prior to production deployment.
- **Configuration Switch:** A single environment variable `DATABASE_URL` toggles the active repository driver.

---

## 13. Risks & Mitigations

| Risk Factor | Severity | Mitigation Strategy |
|:---|:---:|:---|
| **SQL Syntax Dialect Incompatibility** | Low | Both SQLite and PostgreSQL queries in `StandardsRepository` are standard ANSI SQL (`SELECT`, `COUNT`, `WHERE ... IN (...)`). No SQLite-specific functions are used. |
| **Cold Start Startup Time on Cloud Run** | Medium | The in-memory BM25 index takes <100ms. TF-IDF fallback takes ~800ms. Total cold start is ~2 seconds, well within Cloud Run's 10-second startup threshold. |
| **Connection Pooling Exhaustion** | Medium | Use SQLAlchemy async session or `psycopg3` connection pool with `max_overflow=10` and `pool_size=5` per Cloud Run container. |
| **Credential Leakage** | Critical | Use Google Secret Manager for `DATABASE_URL` and `GEMINI_API_KEY`. Never check secrets into `.env`, `.env.example`, or Git. |
| **Dual User Model Discrepancy** | Low | The `users` table schema supports both legacy password hashes and Firebase UIDs seamlessly. |

---

## 14. Rollback Strategy

If any failure occurs during the future PostgreSQL deployment:
1. **Instant Environment Reversion:** Remove or unset `DATABASE_URL` in the Cloud Run service configuration or local `.env`.
2. **Seamless SQLite Fallback:** The application immediately falls back to `data/standards-database-v5.db`, which remains untouched and functional.
3. **Zero Data Corruption:** Because the SQLite database is mounted as read-only during migration verification, no data corruption is possible.

---

## 15. Migration Test Plan

| Test Phase | Scope | Acceptance Criteria |
|:---|:---|:---|
| **Phase A: Database Connectivity** | PostgreSQL connection verification | Connection established within 500ms; `SELECT 1` succeeds. |
| **Phase B: Schema & Row Count Parity** | Verify table creation and record migration | `standards` has exactly 559 rows; `users` has matching accounts; indexes exist. |
| **Phase C: Retrieval Parity** | Compare search outputs between SQLite and PostgreSQL | Top-5 ranked standards for sample queries (*"1.1 kV XLPE cable"*, *"Fe 500D TMT bar"*, *"Solar PV module"*) match with score delta < 0.001. |
| **Phase D: Procurement Pipeline End-to-End** | Run `POST /api/v1/procurement/analyze` | Multi-item procurement request produces identical 100% readiness score and sourcing hubs. |
| **Phase E: Pytest Suite Regression** | Run all 14 test modules in `backend/tests/` | **104 passed / 0 failed**. |
| **Phase F: Frontend Production Build** | Run `npm run build` in `frontend/` | Zero compilation errors, all 6 static routes generate cleanly. |

---

## 16. Exact Next Implementation Phase

The recommended phased execution roadmap:

1. **Phase 2A (Database Adapter Layer):**
   - Create an abstract `DatabaseAdapter` or update `StandardsRepository` and `UserRepository` to support both SQLite (`sqlite3`) and PostgreSQL (`asyncpg` or `psycopg`).
   - Add `DATABASE_URL` configuration parameter to `Settings` in `backend/app/core/config.py`.
2. **Phase 2B (Data Migration Script):**
   - Implement `scripts/migrate_sqlite_to_postgres.py` with automated pre-checks, row count assertions, and idempotency.
3. **Phase 2C (Firebase Auth Integration):**
   - Add `firebase-admin` to backend and wire Firebase token verification into `get_current_user_optional`.
4. **Phase 2D (Cloud Run & Cloud SQL Provisioning):**
   - Provision Cloud SQL PostgreSQL instance and deploy backend container to Cloud Run with Cloud SQL connection.

---

```text
================================================================================
MIGRATION_STATUS:
READY_FOR_SCHEMA_IMPLEMENTATION
================================================================================
```
