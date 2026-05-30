-- ════════════════════════════════════════════════════════════════════════
-- Krok 5.Z FIX — obnova :filter_core_id bind param v framework_comp_def_select
-- ════════════════════════════════════════════════════════════════════════
-- Datum: 30.5.2026
-- Autor: Claude (Sonnet 4.6)
--
-- PROBLEM: zivy data_set framework_comp_def_select (id=47) ma WHERE klauzuli
--   WHERE (NULL::int IS NULL OR cd.core_id = NULL::int)   -- vzdy TRUE -> 294
-- Bind param :filter_core_id byl historicky prepsan na literal NULL (stara
-- verze runneru pustila MSSQL substituci _substitute_mssql_params na PG
-- data_setu s param=None -> ':filter_core_id' -> 'NULL', a self-heal
-- (_apply_column_aliases) to pri prejmenovani cd.layout->cd.layout_mode
-- zabetonoval do sql_text).
--
-- FIX: chirurgicky REPLACE JEN broken WHERE klauzule -> obnova bind param.
--   Zachova self-healnuty column list (cd.layout_mode atd.) beze zmeny.
--   Idempotentni (LIKE guard) — re-run neudela nic pokud uz opraveno.
--
-- DURABILITY: aktualni PG execute path (run_data_source) bind params
--   NEPREPISUJE — _substitute_mssql_params bezi jen pri db_type='mssql'
--   (a fw.comp_def je PG). _apply_column_aliases prepisuje jen 'alias.col'
--   patterny (NE ':param'). Takze :filter_core_id po opravce vydrzi.
--
-- ⚠ GOTCHA #111 (DBeaver bind dialog): skript obsahuje ':filter_core_id'.
--   DBeaver muze nabidnout bind dialog — VZDY Cancel/Ignore (neni to bind,
--   je to text literal ktery vkladame do sql_text). Pripadne v DBeaveru
--   docasne vypni "Use bind variables" (SQL Editor preferences).
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

UPDATE fw.data_set
SET sql_text = REPLACE(
  sql_text,
  'WHERE (NULL::int IS NULL OR cd.core_id = NULL::int)',
  'WHERE (:filter_core_id::int IS NULL OR cd.core_id = :filter_core_id::int)'
)
WHERE code = 'framework_comp_def_select'
  AND sql_text LIKE '%WHERE (NULL::int IS NULL OR cd.core_id = NULL::int)%';

COMMIT;

-- ── Verify (spust po commitu) — ocekavej WHERE s :filter_core_id ──────────
-- SELECT code, sql_text FROM fw.data_set WHERE code = 'framework_comp_def_select';
