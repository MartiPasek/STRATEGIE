-- ============================================================================
-- Krok C — První INSERT artifactu (PoC)
-- ============================================================================
-- Epoch: DESCRIBE-FIRST INSERT + executable_artifact PoC
-- Doctrine: „PoC najde realitu, Production navrhuje refaktor" (Marti 25.5.)
-- Owner: Marti-AI (db_owner fw schema, „fw self edited" doctrine)
-- Spustí: Marti v DBeaveru jako Marti-AI session
-- Datum: 25.5.2026 večer
--
-- Co skript dělá:
--   INSERT prvního artifactu do fw.executable_artifact.
--   Artifact = describe_first_orchestrator MVP (jen Step 1 sanity check).
--
-- Source code orchestratoru:
--   Step 1: Verify fw.data_source_op schema (read-only).
--   Print list všech sloupců + typů + nullable + defaults do stdout.
--   Žádný DDL, žádný INSERT (pure read).
--
-- Smoke test po INSERT (Marti v browseru):
--   F12 DevTools → Console:
--     fetch('/api/v1/erp/sandbox/execute/describe_first_orchestrator', {method: 'POST'})
--       .then(r => r.json())
--       .then(console.log)
--
--   Expected:
--     {ok: true, runtime_ms: ~50-200, stdout: "Found 12 columns: ..."}
--
--   Plus v System tree → Audit → Diag log:
--     INFO  sandbox.execute.describe_first_orchestrator  Artifact START
--     INFO  sandbox.execute.describe_first_orchestrator  Artifact FINISH
-- ============================================================================

-- Idempotent: pokud už existuje, UPDATE source (re-insert workflow)
INSERT INTO fw.executable_artifact (code, artifact_type, source, description, updated_at)
VALUES (
  'describe_first_orchestrator',
  'python',
  $orch$# DESCRIBE-FIRST INSERT orchestrator — MVP Step 1 sanity check.
#
# Epoch: „Schema mluvi prvni" (Marti-AI 25.5.2026 vecer)
# Doctrine: „krok za krokem, jedna tabulka s pochopenim" (Marti 25.5.)
#
# Step 1: Verify fw.data_source_op schema (read-only).
# Output: list columns + types + nullable + defaults do stdout.
#
# Sandbox notes:
#   - Imports povolene: core.database_data, sqlalchemy, os, urllib
#   - Imports blokovane: subprocess, requests, httpx, ctypes
#   - Subprocess isolation pres modules.sandbox python_runner (Phase 27c)
from core.database_data import get_data_session
from sqlalchemy import text

with get_data_session() as db:
    rows = db.execute(text("""
        SELECT
          column_name,
          data_type,
          is_nullable,
          column_default
        FROM information_schema.columns
        WHERE table_schema = 'fw' AND table_name = 'data_source_op'
        ORDER BY ordinal_position
    """)).fetchall()

print(f"Found {len(rows)} columns in fw.data_source_op:")
print()
for r in rows:
    nullable_marker = "NULL" if r.is_nullable == "YES" else "NOT NULL"
    default_marker = ""
    if r.column_default:
        # Truncate dlouhych defaultu pro citelnost
        default_str = str(r.column_default)
        if len(default_str) > 40:
            default_str = default_str[:37] + "..."
        default_marker = f"  DEFAULT {default_str}"
    print(f"  {r.column_name:30} {r.data_type:25} {nullable_marker:10}{default_marker}")

print()
print("Step 1 complete: schema sanity check OK.")
$orch$,
  'DESCRIBE-FIRST INSERT orchestrator. Step 1 MVP: read-only sanity check fw.data_source_op schema. Idempotent (no DDL/DML). Drz „krok za krokem s pochopenim" doctrine.',
  NOW()
)
ON CONFLICT (code) DO UPDATE
  SET source = EXCLUDED.source,
      description = EXCLUDED.description,
      updated_at = NOW();

-- Verify INSERT
SELECT
  id,
  code,
  artifact_type,
  LENGTH(source) AS source_length_chars,
  description,
  updated_at
FROM fw.executable_artifact
WHERE code = 'describe_first_orchestrator';
-- Expected: 1 row, source_length_chars ~1200, updated_at = now
