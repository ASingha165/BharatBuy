import os
import sys
import json
import hashlib
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor

# Ensure backend can be imported
sys.path.insert(0, os.path.abspath("."))
from backend.app.core.config import settings

def run_deep_parity_audit():
    print("=" * 70)
    print("BHARATBUY AUDIT 1: DEEP NEON POSTGRESQL PARITY AUDIT")
    print("=" * 70)

    db_url = settings.DATABASE_URL
    if not db_url:
        print("[FAIL] DATABASE_URL is not set!")
        sys.exit(1)

    sqlite_path = settings.DATABASE_PATH
    if not os.path.exists(sqlite_path):
        print(f"[FAIL] SQLite database not found at {sqlite_path}")
        sys.exit(1)

    # 1. Connect to SQLite
    sq_conn = sqlite3.connect(sqlite_path)
    sq_conn.row_factory = sqlite3.Row
    sq_cur = sq_conn.cursor()

    # 2. Connect to Neon PostgreSQL
    pg_conn = psycopg2.connect(db_url)
    pg_cur = pg_conn.cursor(cursor_factory=RealDictCursor)

    # ---------------------------------------------------------
    # PART A: STANDARDS TABLE FULL FIELD-BY-FIELD AUDIT
    # ---------------------------------------------------------
    print("\n--- STANDARDS CATALOG AUDIT ---")
    columns = [
        "standard_id",
        "is_code",
        "title",
        "department",
        "scope_summary",
        "key_specifications",
        "testing_requirements",
        "status",
        "publication_year"
    ]

    sq_cur.execute(f"SELECT {', '.join(columns)} FROM standards ORDER BY standard_id ASC")
    sq_rows = sq_cur.fetchall()
    sq_standards = {r["standard_id"]: dict(r) for r in sq_rows}

    pg_cur.execute(f"SELECT {', '.join(columns)} FROM standards ORDER BY standard_id ASC")
    pg_rows = pg_cur.fetchall()
    pg_standards = {r["standard_id"]: dict(r) for r in pg_rows}

    print(f"SQLite total standards:      {len(sq_standards)}")
    print(f"PostgreSQL total standards:  {len(pg_standards)}")

    if len(sq_standards) != 559 or len(pg_standards) != 559:
        print(f"[FAIL] Expected 559 standards, got SQLite={len(sq_standards)}, PG={len(pg_standards)}")
        sys.exit(1)
    else:
        print("[PASS] Exact 559 row count verified.")

    # ID set comparison
    sq_ids = set(sq_standards.keys())
    pg_ids = set(pg_standards.keys())

    diff_in_sq = sq_ids - pg_ids
    diff_in_pg = pg_ids - sq_ids
    if diff_in_sq or diff_in_pg:
        print(f"[FAIL] ID mismatch! In SQLite only: {diff_in_sq}, In PG only: {diff_in_pg}")
        sys.exit(1)
    else:
        print("[PASS] All 559 Primary Keys match 100%.")

    # Column-by-column deep content comparison
    discrepancies = []
    for sid, sq_data in sq_standards.items():
        pg_data = pg_standards[sid]
        for col in columns:
            sq_val = sq_data.get(col)
            pg_val = pg_data.get(col)
            # Normalize whitespace/None
            sq_norm = str(sq_val).strip() if sq_val is not None else ""
            pg_norm = str(pg_val).strip() if pg_val is not None else ""
            if sq_norm != pg_norm:
                discrepancies.append((sid, col, sq_norm[:30], pg_norm[:30]))

    if discrepancies:
        print(f"[FAIL] Found {len(discrepancies)} field discrepancies across standards!")
        for d in discrepancies[:5]:
            print(f"   Standard: {d[0]}, Col: {d[1]}, SQLite: '{d[2]}', PG: '{d[3]}'")
        sys.exit(1)
    else:
        print("[PASS] 100% field-by-field parity across all 9 retrieval fields for all 559 standards.")

    # MD5 Checksum of all records serialized
    sq_serialized = json.dumps([sq_standards[k] for k in sorted(sq_standards.keys())], sort_keys=True)
    pg_serialized = json.dumps([pg_standards[k] for k in sorted(pg_standards.keys())], sort_keys=True)
    sq_md5 = hashlib.md5(sq_serialized.encode("utf-8")).hexdigest()
    pg_md5 = hashlib.md5(pg_serialized.encode("utf-8")).hexdigest()
    print(f"SQLite Full Data Checksum:   {sq_md5}")
    print(f"PostgreSQL Data Checksum:    {pg_md5}")
    if sq_md5 == pg_md5:
        print("[PASS] Cryptographic dataset checksum match: 100% identical.")
    else:
        print("[FAIL] Cryptographic checksum mismatch!")
        sys.exit(1)

    # ---------------------------------------------------------
    # PART B: SOURCING SOURCES PARITY & DEMO ISOLATION
    # ---------------------------------------------------------
    print("\n--- SOURCING SOURCES & DEMO ISOLATION AUDIT ---")
    pg_cur.execute("SELECT source_id, source_name, source_type, city, state, verification_status FROM sourcing_sources ORDER BY source_id ASC")
    pg_sources = pg_cur.fetchall()
    print(f"PostgreSQL sourcing_sources count: {len(pg_sources)}")

    registry_path = "data/sourcing-registry-v1.json"
    with open(registry_path, "r", encoding="utf-8") as f:
        auth_registry = json.load(f)
    print(f"Authentic Registry JSON count:   {len(auth_registry)}")

    auth_ids = {r["source_id"] for r in auth_registry}
    pg_source_ids = {r["source_id"] for r in pg_sources}

    if len(pg_sources) != 17 or pg_source_ids != auth_ids:
        print(f"[FAIL] Sourcing records mismatch! Expected {len(auth_ids)}, got {len(pg_source_ids)}")
        sys.exit(1)
    else:
        print("[PASS] Exact 17 authentic sourcing entities verified in PostgreSQL.")

    # Check Demo Isolation
    demo_registry_path = "data/demo-sourcing-registry-v1.json"
    with open(demo_registry_path, "r", encoding="utf-8") as f:
        demo_registry = json.load(f)
    demo_ids = {r["source_id"] for r in demo_registry}
    print(f"Demo Registry IDs to check:      {demo_ids}")

    leak_in_pg = demo_ids.intersection(pg_source_ids)
    if leak_in_pg:
        print(f"[FAIL] Demo entities leaked into production PostgreSQL: {leak_in_pg}")
        sys.exit(1)
    else:
        print("[PASS] Zero demo entities exist in production PostgreSQL. Strict isolation verified.")

    # ---------------------------------------------------------
    # PART C: USER RECORDS AUDIT
    # ---------------------------------------------------------
    print("\n--- USER RECORDS AUDIT ---")
    pg_cur.execute("SELECT id, name, email, organization, firebase_uid, created_at FROM users")
    users = pg_cur.fetchall()
    print(f"PostgreSQL users count: {len(users)}")
    for u in users:
        print(f"   User ID: {u['id']}, Email: {u['email']}, Name: {u['name']}, Org: {u['organization']}, Firebase UID: {u['firebase_uid']}")

    print("\n" + "=" * 70)
    print("[SECTION 1 AUDIT RESULT] PASS: 100% NEON DATA PARITY & INTEGRITY VERIFIED")
    print("=" * 70)

    sq_conn.close()
    pg_conn.close()

if __name__ == "__main__":
    run_deep_parity_audit()
