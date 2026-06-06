-- ============================================================================
-- Krok C reality pivot — orchestrator hello-world (NO DB access)
-- ============================================================================
-- Marti's smoke 25.5.2026 vecer odhalil:
--   ModuleNotFoundError: No module named 'core'
--
-- Root cause: modules/sandbox/application/python_runner.py line 575-582
--   subprocess sub_env = sanitized, no PYTHONPATH
--   ("rely on installed packages")
--
-- Pivot: pro PoC pipeline validation drz orchestrator MINIMAL — jen
--   stdlib + print. Žádný DB access. Až bude pipeline ZELENA, vyresime
--   DB access pattern v Kroku D (PYTHONPATH extension nebo psycopg2 +
--   inject DATABASE_URL pres sub_env).
--
-- Marti's doctrine: „PoC najde realitu, Production navrhuje refaktor"
-- ============================================================================

UPDATE fw.executable_artifact
SET source = $orch$# DESCRIBE-FIRST INSERT orchestrator — Hello World pipeline validation
#
# Epoch: „Schema mluvi prvni" (Marti-AI 25.5.2026 vecer)
# Doctrine: „krok za krokem, jedna tabulka s pochopenim" (Marti 25.5.)
#
# PoC discovery (Marti's smoke 25.5. vecer):
#   Sandbox subprocess je isolated bez PYTHONPATH = no `core.database_data`.
#   Solution defer: v Kroku D resolvneme (PYTHONPATH inject nebo
#   psycopg2 + DATABASE_URL pres sub_env extension).
#
# Tento MVP: pure stdlib + print pro pipeline validation.
import sys
import os
import datetime

print("=== DESCRIBE-FIRST INSERT orchestrator (PoC hello-world) ===")
print()
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Current working directory: {os.getcwd()}")
print(f"Available env vars: {sorted(os.environ.keys())}")
print(f"Timestamp: {datetime.datetime.now().isoformat()}")
print()
print("Pipeline validation:")
print("  ✓ fw.executable_artifact INSERT proběhl (orchestrator je tady)")
print("  ✓ API endpoint POST /sandbox/execute/<code> dispatched (vidíme stdout)")
print("  ✓ sandbox subprocess runs (Python is alive)")
print("  ✓ stdout capture works (čtete tento výstup)")
print()
print("Next step (Krok D): DB access pattern decision")
print("  - Option A: extend sandbox sub_env with PYTHONPATH (opt-in flag)")
print("  - Option B: psycopg2 direct + DATABASE_URL inject")
print("  - Option C: backend orchestrator (bypass sandbox)")
print()
print("Step 1 hello-world complete: pipeline LIVE end-to-end.")
$orch$,
    description = 'PoC hello-world: pipeline validation pres sandbox (žádný DB access yet). Krok D = DB access pattern decision.',
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
-- Expected: 1 row, source_length_chars ~1100, updated_at = teď
