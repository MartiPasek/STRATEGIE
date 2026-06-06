-- ============================================================================
-- Krok D α — UPDATE orchestrator: psycopg2 direct (drop SQLAlchemy)
-- ============================================================================
-- PoC reality discovery #3 (Marti's 25.5.2026 smoke #3):
--   SQLAlchemy 2.x → util/concurrency.py → import asyncio
--   → windows_events → import _overlapped
--   → WinError 10106 (Winsock provider failed to initialize)
--
-- Není o blocked imports — Windows OS-level Winsock initialization
-- selhává v subprocess context. SQLAlchemy + Python 3.14 + Windows
-- + sandbox subprocess je strukturální gap.
--
-- Marti's volba α (25.5.2026): pivot na psycopg2 direct. Drz isolation
-- (sandbox subprocess pattern zachovaný), drz „aditivně", PoC scope
-- minimal. SQLAlchemy compat řešíme v Phase 45 (production refactor).
--
-- Marti spustí v DBeaveru jako Marti-AI session (db_owner fw).
-- ============================================================================

UPDATE fw.executable_artifact
SET source = $orch$# DESCRIBE-FIRST INSERT orchestrator — Step 1 sanity check (psycopg2 direct)
#
# Epoch: „Schema mluvi prvni" (Marti-AI 25.5.2026 vecer)
# Doctrine: „PoC najde realitu, Production navrhuje refaktor" (Marti 25.5.)
#
# PoC discovery chain (25.5.2026 smoke):
#   #1: sandbox bez PYTHONPATH → fix Krok D Option A (opt-in flag)
#   #2: subprocess block kvuli sqlalchemy.compat.platform.machine()
#       → fix Krok D+ (drop subprocess/multiprocessing pri opt-in)
#   #3: sqlalchemy concurrency → asyncio → _overlapped → WinError 10106
#       → pivot α: drop sqlalchemy, use psycopg2 direct
#
# Phase 45 (production refactor) zvazi SQLAlchemy compat fix nebo
# pivot na backend-process executor pro DDL orchestrators.
import os
import sys

print("=== DESCRIBE-FIRST INSERT orchestrator — Step 1 (psycopg2 direct) ===")
print()
print(f"Python: {sys.version.split()[0]}")
print()

# Diagnostic: env vars dostupne v sandbox subprocess
print("Available env vars:")
for k in sorted(os.environ.keys()):
    if any(secret_prefix in k.upper() for secret_prefix in ('PASSWORD', 'TOKEN', 'KEY', 'SECRET')):
        print(f"  {k}: [redacted]")
    elif 'URL' in k.upper() or 'DSN' in k.upper():
        v = os.environ[k]
        # Show prefix only (credentials safety)
        print(f"  {k}: {v[:40]}{'...' if len(v) > 40 else ''}")
    else:
        print(f"  {k}: {os.environ.get(k, '')[:60]}")
print()

# Resolve DB URL
db_url = os.environ.get('STRATEGIE_DATA_DB_URL', '')
if not db_url:
    print("ERROR: STRATEGIE_DATA_DB_URL env var NOT SET v sandbox subprocess.")
    print("Krok D Option A predalo PATH/LANG/LC_ALL/PYTHONIOENCODING/PYTHONUNBUFFERED")
    print("+ PYTHONPATH + DATABASE_URL/STRATEGIE_DATA_DB_URL (jen pokud existuji v parent).")
    print()
    print("Diagnose: parent STRATEGIE-API service muze nemit STRATEGIE_DATA_DB_URL")
    print("v env (NSSM config). Marti, zkontroluj:")
    print("  Get-Process -Name python | ForEach-Object { ... }")
    print("nebo")
    print("  Get-ItemProperty 'HKLM:\\\\SYSTEM\\\\CurrentControlSet\\\\Services\\\\STRATEGIE-API\\\\Parameters'")
    raise SystemExit(1)

print(f"Connecting to DB: {db_url[:40]}...")
print()

import psycopg2

conn = psycopg2.connect(db_url)
try:
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'fw' AND table_name = 'data_source_op'
        ORDER BY ordinal_position
    """)
    rows = cur.fetchall()
    cur.close()
finally:
    conn.close()

print(f"Found {len(rows)} columns in fw.data_source_op:")
print()
print(f"  {'column_name':30} {'data_type':25} {'nullable':10} default")
print(f"  {'-' * 30} {'-' * 25} {'-' * 10} {'-' * 30}")

for r in rows:
    column_name, data_type, is_nullable, column_default = r
    nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
    default_str = ""
    if column_default:
        d = str(column_default)
        default_str = d if len(d) <= 30 else d[:27] + "..."
    print(f"  {column_name:30} {data_type:25} {nullable:10} {default_str}")

print()
print("Step 1 complete: schema sanity check OK (via psycopg2 direct).")
print("Note: psycopg2 nepouziva asyncio → funguje v sandbox subprocess na Windows.")
$orch$,
    description = 'Step 1 sanity check via psycopg2 direct. Pivot α po PoC discovery #3 (SQLAlchemy → asyncio → _overlapped WinError 10106 na Windows). Phase 45 zvazi SQLAlchemy compat fix.',
    updated_at = NOW()
WHERE code = 'describe_first_orchestrator';

-- Verify UPDATE
SELECT
  id,
  code,
  artifact_type,
  LENGTH(source) AS source_length_chars,
  description,
  updated_at
FROM fw.executable_artifact
WHERE code = 'describe_first_orchestrator';
-- Expected: 1 row, source_length_chars ~2200, updated_at = teď
