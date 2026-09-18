# BharatBuy — Project Size Audit & 5.6 GB Vercel Root Cause Analysis

**Date**: 2026-09-19  
**Auditor**: Antigravity AI  
**Scope**: Complete repository inventory across backend, frontend, data, models, dependencies, and caches.

---

## 1. Executive Summary

- **Total Repository Size on Disk**: **1,167.35 MB** (~1.17 GB)
- **Vercel Reported Deployment Size**: **5,622.28 MB** (~5.62 GB)
- **Vercel Serverless Function Limit**: 250 MB uncompressed (exceeded by ~22.5x)
- **Exact Root Cause**: The inclusion of `torch>=2.2.0` and `sentence-transformers>=2.5.0` in `backend/requirements.txt`. In a Linux serverless container (Amazon Linux / Debian used by Vercel), standard `pip install torch` downloads the PyTorch wheel (~800 MB compressed) plus the entire NVIDIA CUDA 12 runtime family (`nvidia-cublas-cu12`, `nvidia-cudnn-cu12`, `nvidia-cuda-nvrtc-cu12`, `nvidia-cufft-cu12`, `nvidia-curand-cu12`, `nvidia-cusolver-cu12`, `nvidia-cusparse-cu12`, `triton`). These unpack to **~5.2 GB** in `site-packages`, inflating the container bundle to exactly **5,622.28 MB**.

---

## 2. Complete Repository Directory Inventory

| Path / Item | Type | Size (MB) | Category / Description |
| :--- | :--- | :--- | :--- |
| `frontend/` | Directory | **710.58 MB** | Next.js 14 Web Application |
| `backend/` | Directory | **455.51 MB** | FastAPI Python API Server |
| `.git/` | Directory | **0.51 MB** | Git repository metadata |
| `data/` | Directory | **0.45 MB** | BIS Standards DB (v5) + Sourcing Registries |
| `stitch_bharatbuy_ai_procurement_intelligence_ui/` | Directory | **0.13 MB** | UI design export archive |
| `AGENTS.md` | File | **0.04 MB** | Living project memory & architecture spec |
| `CLOUD_MIGRATION_AUDIT.md` | File | **0.03 MB** | Cloud migration assessment |
| `README.md` | File | **0.02 MB** | Developer guide & documentation |
| `FINAL_BHARATBUY_CLOUD_READINESS.md` | File | **0.02 MB** | Cloud integration documentation |
| `.pytest_cache/` | Directory | **0.02 MB** | Temporary pytest cache (root) |
| `CLOUD_AUTH_DATA_INTEGRATION_REPORT.md`| File | **0.01 MB** | Cloud auth integration report |
| `CLOUD_MIGRATION_PHASE2.md` | File | **0.01 MB** | Cloud migration phase 2 notes |
| `DEMO_SCRIPT.md` | File | **0.01 MB** | Demo walkthrough script |
| `firestore.rules` | File | **0.005 MB** | Cloud Firestore security rules |
| `backend_live.log` | File | **0.004 MB** | Temporary execution log |
| `backend_live_err.log` | File | **0.001 MB** | Temporary error log |
| `docs/` | Directory | **0.001 MB** | Documentation directory |
| `.env.example` | File | **0.002 MB** | Config template |
| `.env` | File | **0.001 MB** | Local environment config |
| `docker-compose.yml` | File | **0.001 MB** | Container orchestration file |
| `.gitignore` | File | **0.001 MB** | Git ignore rules |
| `package.json` | File | **0.001 MB** | Root workspace npm scripts |
| `models/` | Directory | **0.000 MB** | Custom model placeholder (`.gitkeep` only) |
| `.vercelignore` | File | **0.000 MB** | Vercel exclusion rules |
| `firebase.json` | File | **0.000 MB** | Firebase project configuration |
| **TOTAL REPOSITORY** | — | **1,167.35 MB** | — |

---

## 3. Subdirectory Footprint Breakdown

### A. Backend (`backend/` — 455.51 MB)
- `backend/.venv/`: **454.05 MB** (99.7% of backend size — local Python virtual environment)
- `backend/tests/`: **0.80 MB** (23 automated test modules)
- `backend/app/`: **0.61 MB** (FastAPI application source code)
- `backend/scripts/`: **0.04 MB** (migration & parity verification scripts)
- `backend/.pytest_cache/`: **0.01 MB** (test cache)
- `backend/Dockerfile`, `vercel.json`, `requirements.txt`: **< 0.01 MB**

### B. Backend Installed Python Packages (`backend/.venv/Lib/site-packages` — 441 MB)
The largest packages currently installed in the backend environment:

| Package | Installed Size (MB) | Purpose & Usage | Classification |
| :--- | :--- | :--- | :--- |
| `scipy` + `scipy.libs` | **128.53 MB** | Transitive dependency of `scikit-learn` | REQUIRED for TF-IDF / cosine sim |
| `googleapiclient` + `google` | **141.09 MB** | Google Cloud / Firebase Admin / Gemini SDK | REQUIRED for Auth / Cloud APIs |
| `numpy` + `numpy.libs` | **51.19 MB** | Numerical operations & vector math | REQUIRED |
| `sklearn` (scikit-learn) | **40.40 MB** | TF-IDF vectorizer fallback | REQUIRED for lightweight semantic |
| `grpc` | **12.55 MB** | gRPC transport for Google Cloud | REQUIRED |
| `pip` | **10.51 MB** | Package installer inside virtualenv | DEV ONLY |
| `cryptography` | **10.49 MB** | Security / Auth crypto | REQUIRED |
| `pygments` | **8.07 MB** | Syntax highlighting (pytest/rich) | DEV/TEST ONLY |
| `psycopg2_binary.libs` | **6.24 MB** | PostgreSQL / Neon DB driver | REQUIRED |
| `pydantic` + `pydantic_core`| **8.76 MB** | Schema validation | REQUIRED |
| `_pytest` | **2.83 MB** | Test framework | TEST ONLY |
| `fastapi` + `starlette` | **2.10 MB** | Web framework | REQUIRED |
| `uvicorn` | **1.80 MB** | ASGI server | REQUIRED |
| `firebase_admin` | **1.14 MB** | Firebase token validation | REQUIRED |

*(Notice: `torch` and `sentence-transformers` were omitted from this local `.venv`, which is why this environment is only 454 MB instead of 5,622 MB).*

### C. Frontend (`frontend/` — 710.58 MB)
- `frontend/node_modules/`: **432.49 MB** (Next.js, React, Leaflet, React Flow, Firebase SDK)
- `frontend/.next/`: **277.68 MB** (Next.js build artifacts & compiler cache)
- `frontend/components/`: **0.18 MB** (15 active React components)
- `frontend/package-lock.json`: **0.11 MB**
- `frontend/app/`: **0.05 MB** (Next.js App router pages: layout, home, signin, signup)
- `frontend/lib/`: **0.04 MB** (API client, Firebase, Firestore, map config, auth context)
- `frontend/types/`: **0.01 MB** (TypeScript definitions)

### D. Active Data Assets (`data/` — 0.45 MB)
- `data/standards-database-v5.db`: **400.0 KB** (Active BIS SQLite database containing 559 standards)
- `data/seed_standards.py`: **31.2 KB** (Reproducible standards database generator)
- `data/sourcing-registry-v1.json`: **15.1 KB** (Authentic manufacturer entities & industrial corridors)
- `data/standards-knowledge-graph-v5.json`: **8.6 KB** (Knowledge graph relations)
- `data/demo-sourcing-registry-v1.json`: **2.6 KB** (Isolated demo mode registry)

---

## 4. Root Cause of 5,622.28 MB Vercel Bundle

1. **Previous `requirements.txt` specification**:
   In commit `c3178d4`, `backend/requirements.txt` contained:
   ```txt
   sentence-transformers>=2.5.0
   torch>=2.2.0
   ```
2. **Serverless Linux Wheel Expansion**:
   When deployed with `@vercel/python` on Linux, PyTorch does not install a CPU-only stub by default unless special index URLs are specified. Pip installs the full CUDA-enabled package plus transitive dependencies:
   - `torch` core wheel: ~900 MB
   - `nvidia-cudnn-cu12`: ~700 MB
   - `nvidia-cublas-cu12`: ~450 MB
   - `nvidia-cusparse-cu12`, `nvidia-cusolver-cu12`, etc.: ~900 MB
   - `triton`: ~400 MB
   - `sentence-transformers`, `transformers`, `tokenizers`, `huggingface-hub`: ~600 MB
   - Base packages (`scipy`, `googleapiclient`, `numpy`, `sklearn`): ~450 MB
   - Transitive download cache & extracted artifacts: ~1,200 MB
   **Total bundle size: 5,622.28 MB.**
3. **Architectural Redundancy**:
   BharatBuy's recommendation and retrieval engine (`HybridRetrievalService`) already has:
   - Okapi BM25 ranking (`BM25Okapi`)
   - TF-IDF vector retrieval (`sklearn.feature_extraction.text.TfidfVectorizer`)
   - Baseline term and category matching
   - Deterministic multi-factor scoring
   SentenceTransformers and CrossEncoder are optional accelerators that are not required for standard procurement analysis.

---

## 5. Optimization Target & Strategy

| Layer | Action |
| :--- | :--- |
| **Requirements** | Split into `requirements.txt` (lean production core, ~150 MB installed), `requirements-ml.txt` (optional heavy ML), and `requirements-test.txt` (pytest). |
| **Imports** | Enforce lazy loading in `embedding_service.py` and `reranker_service.py` so PyTorch is never imported unless explicitly requested. |
| **Data** | Retain only active V5 database (`standards-database-v5.db`), active graph, and active sourcing registries. Total runtime data: < 0.5 MB. |
| **Deployment Artifact** | Package only `backend/app/`, `data/`, and production `requirements.txt` into a clean, measured lean bundle (< 1.5 MB uncompressed source, without virtualenv). |
