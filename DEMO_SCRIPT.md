# BharatBuy / SIH26108: Official Production Demo Script
**3–5 Minute Presentation & Live Demonstration Guide for Evaluators and Jury**

---

## 1. Executive Summary & Opening Statement (30 seconds)
> *"Judges, in Indian startup and enterprise procurement, compliance failure is catastrophic. A tender delivered with non-compliant steel, counterfeit solar panels, or uncertified cables results in rejected shipments, safety hazards, and statutory penalties under Quality Control Orders (QCOs).*
> 
> *BharatBuy solves this by combining **559 indexed Indian Standards (BIS)**, **hybrid retrieval (BM25 + Semantic Vectors)**, and **traceable Sourcing Intelligence**. Critically, BharatBuy enforces **Zero Fabrication**: it separates Product Suitability from Source Trust, never fakes live BIS certificates, and produces human-governed procurement decisions.*
> 
> *Let's see BharatBuy in action across our three enterprise presets."*

---

## 2. Live Demo Flow (3 Minutes)

### Step 1: System Status & Demo Mode Transparency (20s)
1. **Show Top Navigation Header**:
   - Point out **`BHARATBUY / AI PROCUREMENT INTELLIGENCE`**.
   - Point to the live status pills: `System Ready`, `559 Standards Indexed`, `Hybrid BM25+Vector`.
   - Point out the **`PRODUCTION REGISTRY`** pill (or `DEMO MODE ACTIVE` if running with demo data enabled).
2. **Talking Point**:
   > *"Notice the indicator in the header. BharatBuy isolates authentic production data from demo scenarios. When `BHARATBUY_DEMO_MODE=false`, zero synthetic mock suppliers can ever leak into buyer recommendations."*

---

### Step 2: Preset 1 — SOLAR PROJECT (1 minute)
1. **Select Preset**: Click the **`SOLAR PROJECT`** card.
   - Company: `SunVayu CleanEnergy Ltd`
   - Line items auto-populate:
     1. Crystalline silicon terrestrial solar PV modules (IS 14286 / CRS mandatory)
     2. Grid-tied solar inverters (IS 16221)
     3. 1.1 kV XLPE insulated solar DC power cables (IS 7098 Part 1)
     4. Galvanized steel solar mounting structures (IS 2062)
2. **Click `ANALYZE PROCUREMENT`**:
   - Point out the **Multi-Stage Animated Pipeline Indicator**:
     - *Stage 1: Normalizing specifications & physical units...*
     - *Stage 2: Querying 559 Indian Standards in SQLite database...*
     - *Stage 3: Evaluating statutory compliance & BIS testing clauses...*
     - *Stage 4: Mapping registered Indian manufacturing corridors...*
     - *Stage 5: Synthesizing evidence-backed procurement briefing...*
3. **Show Results View**:
   - **5-Metric Coverage Grid**:
     - Standards Coverage (100%)
     - Compliance Coverage (100%)
     - Sourcing Coverage (100%)
     - Evidence Coverage (100%)
     - Verification Coverage
   - **Procurement Decision Badge**:
     - Status: `READY WITH VERIFICATION` (Amber badge).
     - Text: *"Package Decision: READY WITH VERIFICATION. Suitable sourcing identified; verification required before buyer approval."*
4. **Talking Point**:
   > *"Notice the decision language. We strictly eliminate reckless claims like 'Immediate PO release permitted'. Because central PSU manufacturers have documented factory facilities, their live operational CML validity must still be audited on the official BIS portal before buyer approval."*

---

### Step 3: Leaflet Geographic Sourcing & Evidence Chain (1 minute)
1. **Interactive Leaflet Map**:
   - Point to the 4-color legend:
     - **Emerald**: Buyer Verified (Live buyer confirmation recorded)
     - **Amber**: Requires Live Verification (documented manufacturing entity on record; live CML check required on portal)
     - **Blue**: Sourcing Region (cluster only; REGION_ONLY != SUPPLIER)
     - **Rose**: Unverified / Commercial supplier (STATIC EVIDENCE != CURRENT VERIFICATION)
   - Click on **Central Electronics Limited (CEL) Sahibabad** or **Peenya Industrial Area**.
2. **Card Distinction**:
   - Contrast the **Manufacturer Card** (CEL Sahibabad) with its CML reference and Gazette backing against the **Sourcing Region Card** (Peenya Cluster).
   - Point out the blue corridor card: *"Sourcing Region Cluster — No supplier-level CML attached. Vendor verification required before buyer approval."*
3. **Inspect Evidence Drawer**:
   - Click **`[VIEW EVIDENCE]`** on CEL Sahibabad.
   - Slide-over opens showing:
     - **Trust Rating**: High Trust (90%) with 4-pillar breakdown (Identity, BIS Documentation, Freshness, Completeness).
     - **Portal Link**: Link to official BIS portal (`manakonline.in`).
     - **Guided 5-Point Buyer Checklist**:
       1. License / reference exists in official BIS database
       2. Product category matches item requirements
       3. Cited Indian Standard is covered in license scope
       4. License is currently valid and operative
       5. Manufacturer name and factory site address match supplier
   - Demonstrate clicking the 5 checkboxes and entering the officer ID `procurement.officer@sunvayu.in`.
   - Click **`Record Buyer Verification (Mark as Confirmed)`**.
   - Show the recorded immutable audit trail entry and the prominent disclaimer:
     > *"Buyer confirmation recorded manually. BharatBuy did not perform automated BIS verification."*

---

### Step 4: Preset 2 — FACTORY CONSTRUCTION & Preset 3 — IT PROCUREMENT (30s)
1. **FACTORY CONSTRUCTION**:
   - Load scenario: Fe 500D TMT Steel Rebar, Portland Pozzolana Cement (PPC), Structural Steel Channels.
   - Matches: **IS 1786** (TMT rebar), **IS 1489 Part 1** (PPC cement), **IS 2062** (Structural steel).
   - Shows heavy manufacturing hubs: **SAIL Bokaro**, **SAIL Bhilai**, **Cement Corporation of India (CCI) Tandur**.
2. **IT / OFFICE PROCUREMENT**:
   - Demonstrates **Compulsory Registration Scheme (CRS)** for electronic products under MeitY QCOs (IS 13252 Part 1 for laptops, IS 16242 Part 1 for UPS systems).
   - Mapped to **ITI Limited Bengaluru** and electronics manufacturing corridors.

---

## 3. Core Architectural & Ethical Talking Points

### 1. Why Static Offline Data Cannot Confirm Live BIS Certification
- BIS licenses undergo regular lifecycle events: renewal, operative suspension, testing review, or expiration.
- A static database cannot predict if a license expired yesterday.
- BharatBuy tracks **FreshnessState** (`CURRENT`, `AGING`, `STALE`, `UNKNOWN`) and marks static registry entries as requiring live confirmation on `manakonline.in`.

### 2. Why Interactive Portal Check is Necessary (Statutory Anti-Bot Compliance)
- The official BIS portal (`manakonline.in`) utilizes interactive CAPTCHA and anti-bot protections to safeguard statutory records.
- Attempting to scrape or bypass this portal violates terms of service and risks providing obsolete certification statuses.
- BharatBuy provides an authenticated, interactive 5-point guided workflow that empowers procurement compliance officers to record immutable audit logs without bypassing security controls.

### 3. Decoupled Dual-Scoring Framework
- **Product Suitability ($S_{\text{suit}}$)**: Category alignment (30%), Indian Standards match (35%), compliance capability (20%), and geographic logistics (15%). Mismatched categories immediately zero out suitability.
- **Source Trust ($T_{\text{score}}$)**: Entity identity verification (40%), BIS documentation (30%), record freshness (15%), and data completeness (15%).
- A distributor may have high suitability for cables, but low trust until an original factory test certificate is provided.

### 4. Human-Governed Decision Semantics
- Automated procurement systems that claim "Purchase authorized" or "Immediate PO release" create severe legal liability for startups.
- BharatBuy enforces 4 states: `READY`, `READY_WITH_VERIFICATION`, `INSUFFICIENT_EVIDENCE`, `NOT_RECOMMENDED`.
- Language is strictly *"Procurement-ready for buyer approval"*.

---

## 4. Verification Checklist for Presenters
- [x] Backend running on `http://localhost:8000` (`python -m uvicorn app.main:app --port 8000 --reload`)
- [x] Frontend running on `http://localhost:3000` (`npm run dev`)
- [x] All 78 backend automated tests passing (`pytest backend/tests/`)
- [x] Frontend production build verified (`npm run build`)
- [x] Static registry records properly qualified as *"documented certification evidence — current validity requires verification"*
- [x] Real-world evidence disclaimer visible near procurement decisions and evidence drawer
- [x] Zero forbidden phrases in UI and API responses
