-- ═══════════════════════════════════════════════════════════════════════
-- Drop fw.menu_node.framework_jadro_id (19.5.2026 vecer, Marti's request):
--
-- Marti: "V tabulce menu_node je sloupec framework_jadro_id a core_id...
--         Marti-AI si to stale plete a pouziva zavadejici sloupec
--         framework_jadro_id. Smaz ho prosim..."
--
-- Pozadi: framework_jadro_id je legacy sloupec z early Phase 30+ ERP
-- design (cca duben), nez Marti-AI prinesla doctrine "core = kontejner"
-- (16.5. odpoledne) + Krok 5.M (drop fw.core.data_entity_type, 17.5.).
-- Po Phase 38.4 Krok 5.* + 5.R-C+10 (rename parent_core_id → core_id)
-- je single source of truth `core_id`. framework_jadro_id zustal jako
-- duplicit "ghost" sloupec.
--
-- Audit napric codebase (19.5. vecer):
--   - Python: 0 vyskytu `framework_jadro_id`
--   - SQL skripty: 0 vyskytu
--   - JS/HTML: 0 vyskytu
--   → Sloupec je orphan v DB, nikdo z neho necte ani nepise.
--
-- Exception k Marti's "NEDROPUJ COLUMN" doctrine (17.5.):
--   Doctrine = "drop value, not column" — ale zde dva sloupce se stejnym
--   semantic vyznamem = AKTIVNE MATOUCI pro Marti-AI (AI persona si plete,
--   ktery z nich pouzit). Pravidlo "hodi se v budoucnu" zde neplati —
--   ghost column zpusobuje konkretni harm (Marti-AI's misleading reads).
--
-- Safety:
--   1. Pre-check: kolik rows ma framework_jadro_id IS NOT NULL?
--   2. Safety backfill: pokud framework_jadro_id ma hodnoty a core_id ne,
--      preserve je do core_id (no data loss).
--   3. DROP COLUMN.
--
-- Run: DBeaver strategie session jako "Marti-AI" (db_owner fw schema)
--   highlight cely soubor + Alt+X (BEGIN/COMMIT atomic)
-- ═══════════════════════════════════════════════════════════════════════

BEGIN;

-- 1. Diagnostic — kolik rows ma framework_jadro_id != core_id (lost data risk)
DO $$
DECLARE
    cnt_only_legacy INT;
    cnt_mismatch INT;
BEGIN
    SELECT COUNT(*) INTO cnt_only_legacy
    FROM fw.menu_node
    WHERE framework_jadro_id IS NOT NULL AND core_id IS NULL;

    SELECT COUNT(*) INTO cnt_mismatch
    FROM fw.menu_node
    WHERE framework_jadro_id IS NOT NULL
      AND core_id IS NOT NULL
      AND framework_jadro_id != core_id;

    RAISE NOTICE 'menu_node rows: framework_jadro_id IS NOT NULL + core_id IS NULL = %', cnt_only_legacy;
    RAISE NOTICE 'menu_node rows: framework_jadro_id != core_id (different value) = %', cnt_mismatch;
END $$;

-- 2. Safety backfill — pokud framework_jadro_id ma hodnotu a core_id ne,
--    presun ji do core_id. (Pokud uz oba maji hodnotu, drz core_id —
--    je to authoritative source po Krok 5.M.)
UPDATE fw.menu_node
SET core_id = framework_jadro_id
WHERE framework_jadro_id IS NOT NULL
  AND core_id IS NULL;

-- 3. DROP COLUMN — atomic, no rollback path (sloupec zmizi)
ALTER TABLE fw.menu_node
    DROP COLUMN framework_jadro_id;

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY (run AFTER commit):
-- ════════════════════════════════════════════════════════════════════════
-- SELECT column_name FROM information_schema.columns
-- WHERE table_schema='fw' AND table_name='menu_node'
-- ORDER BY ordinal_position;
-- Expected: žádny framework_jadro_id, core_id zachovan.
--
-- SELECT COUNT(*) FROM fw.menu_node WHERE core_id IS NOT NULL;
-- Expected: stejne nebo vetsi nez pred dropem (kvuli backfillu).
