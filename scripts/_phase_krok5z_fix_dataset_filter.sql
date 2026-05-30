-- ════════════════════════════════════════════════════════════════════════
-- Krok 5.Z FIX v2 — funkcni :filter_core_id bind v framework_comp_def_select
-- ════════════════════════════════════════════════════════════════════════
-- Datum: 30.5.2026
-- Autor: Claude (Sonnet 4.6)
--
-- ROOT CAUSE (z fw.diag_log 30.5. 11:12): forma ':filter_core_id::int'
-- NEFUNGUJE v runneru ->
--   psycopg2.errors.SyntaxError: syntax error at or near ":"
--   WHERE (:filter_core_id::int IS NULL OR cd.core_id = :filter_core_id::int)
-- Duvody:
--   1) Fix H regex v _normalize_params (r":(\w+)") chyti z '::int' falesny
--      bind param 'int' -> params={filter_core_id, int} -> rozbity render.
--   2) '::' mate SQLAlchemy text() bind parser -> psycopg2 dostane ':' literal.
-- TOTO byl puvodni duvod korupce na 'NULL::int' (nekdo obesel bind param
-- jeho odstranenim -> filtr zabit -> vzdy 294).
--
-- FIX: konvence z funkcnich data_setu (_phase38_4_krok11e):
--   WHERE (CAST(:filter_core_id AS int) IS NULL OR cd.core_id = :filter_core_id)
--   - CAST(...) na IS NULL strane (PG neumi odvodit typ bare paramu pri IS NULL)
--   - bare :filter_core_id na porovnani (PG odvodi int z cd.core_id sloupce)
--   - ZADNE '::' -> Fix H najde jen 'filter_core_id', SQLAlchemy bindne cleanly
--
-- Robustni: dva REPLACE pokryji oba mozne soucasne stavy
--   (:filter_core_id::int  NEBO  NULL::int) -> oba na CAST formu.
-- Idempotentni: pokud uz CAST forma, zadny REPLACE nematchne -> no-op.
--
-- ⚠ GOTCHA #111 (DBeaver bind dialog): skript obsahuje ':filter_core_id'.
--   DBeaver muze nabidnout bind dialog — VZDY Cancel/Ignore.
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

UPDATE fw.data_set
SET sql_text = REPLACE(
      REPLACE(
        sql_text,
        'WHERE (:filter_core_id::int IS NULL OR cd.core_id = :filter_core_id::int)',
        'WHERE (CAST(:filter_core_id AS int) IS NULL OR cd.core_id = :filter_core_id)'
      ),
      'WHERE (NULL::int IS NULL OR cd.core_id = NULL::int)',
      'WHERE (CAST(:filter_core_id AS int) IS NULL OR cd.core_id = :filter_core_id)'
    )
WHERE code = 'framework_comp_def_select'
  AND (sql_text LIKE '%:filter_core_id::int%'
       OR sql_text LIKE '%WHERE (NULL::int IS NULL OR cd.core_id = NULL::int)%');

COMMIT;

-- ── Verify (spust po commitu) — ocekavej CAST(:filter_core_id AS int) ─────
-- SELECT sql_text FROM fw.data_set WHERE code = 'framework_comp_def_select';
