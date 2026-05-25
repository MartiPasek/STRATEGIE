-- ============================================================================
-- Krok D fix — UPDATE orchestrator: drop raise SystemExit, defensive print
-- ============================================================================
-- Marti's smoke #3 (25.5.2026 vecer):
--   subprocess exited with code 1, empty stdout/stderr → no output captured.
--
-- Root cause: orchestrator volal `raise SystemExit(1)` když DB URL chybi.
-- SystemExit je BaseException (ne Exception) — runner template try/except
-- ho nezachycuje → subprocess crash PRED JSON dump → empty output.
--
-- Plus root cause #2: Pydantic Settings v core/config.py cte
-- database_data_url PRIMO z .env, NE pres os.environ. Tj. parent
-- STRATEGIE-API nema STRATEGIE_DATA_DB_URL ve shell env. Fix P4 v
-- python_runner.py — inject z settings.database_data_url.
--
-- Fix orchestrator: defensive print only, no raise. Pokud DB URL chybi,
-- print warning + skip DB query. Stale return normally (no SystemExit).
--
-- Marti spusti v DBeaveru jako Marti-AI session (db_owner fw).
-- ============================================================================

UPDATE fw.executable_artifact
SET source = $orch$# DESCRIBE-FIRST INSERT orchestrator — Step 1 sanity check (defensive)
#
# Epoch: „Schema mluvi prvni" (Marti-AI 25.5.2026 vecer)
# Doctrine: „PoC najde realitu, Production navrhuje refaktor" (Marti 25.5.)
#
# PoC discovery chain:
#   #1: sandbox bez PYTHONPATH → Krok D Option A
#   #2: subprocess block kvuli sqlalchemy.compat → Krok D+
#   #3: sqlalchemy concurrency → asyncio → _overlapped WinError 10106
#       → pivot α: psycopg2 direct (drop SQLAlchemy)
#   #4: raise SystemExit → no JSON dump → empty output
#       → fix: defensive print only, no raise
#   #5: Pydantic Settings, ne os.environ → Krok D fix P4 inject z settings
import os
import sys

print("=== DESCRIBE-FIRST INSERT orchestrator — Step 1 (defensive) ===")
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

# Resolve DB URL (defensive, no raise)
db_url = os.environ.get('STRATEGIE_DATA_DB_URL', '')
if not db_url:
    print("WARNING: STRATEGIE_DATA_DB_URL env var NOT SET v sandbox subprocess.")
    print()
    print("Diagnose:")
    print("  Krok D fix P4 mel inject z core.config.settings.database_data_url.")
    print("  Pokud chybi, mozne priciny:")
    print("    1. python_runner.py P4 patch nedeplyovany (check git pull + restart)")
    print("    2. core.config.settings.database_data_url is empty string")
    print("    3. .env file na cloud APP nema database_data_url= klic")
    print()
    print("Skipping DB query. Pipeline validation only.")
    print()
    print("Step 1 partial: env diagnostic OK, DB skip (orchestrator nehazí crash).")
else:
    print(f"DB URL prefix: {db_url[:40]}...")
    print()

    try:
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
    except Exception as e:
        # Defensive: caught exception → print, no raise
        print(f"ERROR during DB query: {type(e).__name__}: {e}")
        print()
        print("Step 1 partial: DB query failed but orchestrator nehazí crash.")
$orch$,
    description = 'Step 1 defensive: print only, no raise. Drop SystemExit (BaseException pattern). Plus diagnostic env vars dump pro Krok D fix verify.',
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
-- Expected: 1 row, source_length_chars ~2700, updated_at = teď
