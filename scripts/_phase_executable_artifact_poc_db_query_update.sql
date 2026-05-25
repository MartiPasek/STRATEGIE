-- ============================================================================
-- Krok D — UPDATE orchestrator source: vrátit DB query (Step 1 sanity check)
-- ============================================================================
-- Po Krok D Option A LIVE (python_runner.py opt-in PYTHONPATH +
-- /sandbox/execute endpoint passes with_strategie_pythonpath=True),
-- orchestrator může opět `import core.database_data` + read DB.
--
-- Marti spustí v DBeaveru jako Marti-AI session (db_owner fw).
-- ============================================================================

UPDATE fw.executable_artifact
SET source = $orch$# DESCRIBE-FIRST INSERT orchestrator — Step 1 schema sanity check (DB access)
#
# Epoch: „Schema mluvi prvni" (Marti-AI 25.5.2026 vecer)
# Doctrine: „krok za krokem, jedna tabulka s pochopenim" (Marti 25.5.)
#
# PoC milestone: Krok D Option A LIVE → orchestrator má STRATEGIE PYTHONPATH
# + DB env vars. Drz isolation pro Marti-AI's python_exec (default False),
# expand selektivne pro /sandbox/execute trusted path (parent-only).
#
# Step 1: read-only sanity check fw.data_source_op schema.
import sys
from core.database_data import get_data_session
from sqlalchemy import text

print("=== DESCRIBE-FIRST INSERT orchestrator — Step 1 (DB access) ===")
print()
print(f"Python: {sys.version.split()[0]}")
print()

with get_data_session() as db:
    rows = db.execute(text("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'fw' AND table_name = 'data_source_op'
        ORDER BY ordinal_position
    """)).fetchall()

print(f"Found {len(rows)} columns in fw.data_source_op:")
print()
print(f"  {'column_name':30} {'data_type':25} {'nullable':10} default")
print(f"  {'-' * 30} {'-' * 25} {'-' * 10} {'-' * 30}")
for r in rows:
    nullable = "NULL" if r.is_nullable == "YES" else "NOT NULL"
    default_str = ""
    if r.column_default:
        d = str(r.column_default)
        default_str = d if len(d) <= 30 else d[:27] + "..."
    print(f"  {r.column_name:30} {r.data_type:25} {nullable:10} {default_str}")

print()
print("Step 1 complete: schema sanity check OK. PoC LIVE with DB access.")
$orch$,
    description = 'Step 1 sanity check: read-only fw.data_source_op schema. Drz „Schema mluví první" (Marti-AI 25.5.). Po Krok D Option A LIVE.',
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
-- Expected: 1 row, source_length_chars ~1200, updated_at = teď
