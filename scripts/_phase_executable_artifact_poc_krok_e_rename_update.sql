-- ============================================================================
-- Krok E — Rename + Minimal orchestrator
-- ============================================================================
-- Marti's PoC volba (25.5.2026 vecer):
--   - Rename existing 'describe_first_orchestrator' → 'vytvor_edit_jadro'
--   - UPDATE source na MINIMUM: drop psycopg2 + DB query
--   - Just print "Hello z PoC orchestratoru" + return
--   - log_event START/FINISH zajisti backend endpoint automaticky
--
-- Vrstva 1 z Marti's plan:
--   „Zatim vyvola jen popup s message. A zaloguje se. Nic vic."
--
-- Marti spusti v DBeaveru jako Marti-AI session (db_owner fw).
-- ============================================================================

-- Idempotent rename: pokud old code existuje, prejmenuj.
-- Pokud uz je 'vytvor_edit_jadro', skip (no-op).
UPDATE fw.executable_artifact
SET code = 'vytvor_edit_jadro'
WHERE code = 'describe_first_orchestrator'
  AND NOT EXISTS (
    SELECT 1 FROM fw.executable_artifact WHERE code = 'vytvor_edit_jadro'
  );

-- UPDATE source + description (po renamu, NEBO existing 'vytvor_edit_jadro')
UPDATE fw.executable_artifact
SET source = $orch$# Vytvořit edit jádro — PoC orchestrator (Krok E, 25.5.2026 vecer)
#
# Marti's plan:
#   1. Cíl: aktivovat CRUD ikonu C (Nový) v gridu
#   2. Mechanismus: drop-up menu item v ErpDataGrid
#   3. PoC: zatim jen popup s message + log_event (automatic)
#
# Tato verze: MINIMUM. Print Hello message. Bez DB access. Backend
# endpoint /sandbox/execute zaloguje START/FINISH do fw.diag_log
# automaticky (pres core/log_queue).
import sys

print("=" * 60)
print("✨ Vytvořit edit jádro — PoC orchestrator")
print("=" * 60)
print()
print("Status: Live ✓")
print(f"Python: {sys.version.split()[0]}")
print()
print("V tuto chvíli orchestrator pouze zdravím — žádný DB access,")
print("žádná akce v fw schema. Tento minimal krok ověřuje:")
print("  ✓ Drop-up menu item „Vytvořit edit jádro\" je viditelný")
print("    v DESIGN mode v každém gridu (univerzálně fw komponenta)")
print("  ✓ Klik triggeruje POST /api/v1/erp/sandbox/execute/vytvor_edit_jadro")
print("  ✓ Backend načte source z fw.executable_artifact (DB-stored)")
print("  ✓ Sandbox subprocess spustí Python (with_strategie_pythonpath=True)")
print("  ✓ stdout capture pipeline funguje (čteš tento výstup)")
print("  ✓ fw.diag_log audit: START + FINISH automaticky (backend)")
print("  ✓ Frontend popup _confirmDarkDialog s tímto stdout")
print()
print("V dalších iteracích orchestrator přidá:")
print("  - context info (kterého gridu se klik týkal: coreId, rowId)")
print("  - vlastní log_event do fw.diag_log (orchestrator-specific)")
print("  - schema introspection target entity")
print("  - fw.core + fw.comp_def hierarchy INSERT (create edit form)")
print("  - aktivace gridActions.has_insert = true v page-spec")
print()
print("PoC milestone reached: UI wire-up → backend execute → popup OK.")
$orch$,
    description = 'PoC orchestrator MINIMAL (Krok E, 25.5.2026): jen popup hello. Bez DB access. Backend endpoint /sandbox/execute auto-loguje START/FINISH. V dalsich iteracich pridame: context info, schema introspection, fw.core+comp_def INSERT, gridActions.has_insert=true.',
    updated_at = NOW()
WHERE code = 'vytvor_edit_jadro';

-- Verify
SELECT
  id,
  code,
  artifact_type,
  LENGTH(source) AS source_length_chars,
  description,
  updated_at
FROM fw.executable_artifact
WHERE code IN ('vytvor_edit_jadro', 'describe_first_orchestrator');
-- Expected: 1 row, code='vytvor_edit_jadro', source_length_chars ~1800
