-- ============================================================
-- DIAG: Krok 5.W DELETE paradox (23.5.2026)
-- ============================================================
-- Backend říká "deleted 1 rows id=1730 schema=fw table=diag_log",
-- ale row 1730 je v fw.diag_log STÁLE PŘÍTOMNÁ.
--
-- Hypotézy:
--   A) _resolve_entity_config_for_core(44) parse vrátil WRONG table
--      (např. jiné jádro 44 než diag_log, nebo SQL parse mismatch)
--   B) Strategie role transakce silently rollback po commit
--   C) Trigger BEFORE DELETE blokuje (RAISE NOTICE bez RAISE EXCEPTION)
--   D) RLS policy blokuje DELETE silently
--   E) Sequence reset re-creates row se stejným ID (unlikely)
--
-- Spusteni: highlight per dotaz + Alt+X
-- ============================================================


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q1: Co je core_id=44? (Marti's screenshot autoLoadDefault)║
-- ╚══════════════════════════════════════════════════════════╝
SELECT
    c.id AS core_id,
    c.code AS core_code,
    c.label
FROM fw.core c
WHERE c.id = 44;


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q2: Jaká data_source + data_set + SQL je na core_44?    ║
-- ║      (= co backend resolver vidí)                         ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT
    c.id AS core_id,
    c.code AS core_code,
    cd.id AS comp_def_id,
    cd.name AS comp_def_name,
    cd.region_slot,
    cd.is_active,
    ds.id AS data_source_id,
    ds.code AS data_source_code,
    op.operation_kind,
    op.is_default,
    dset.id AS data_set_id,
    dset.code AS data_set_code,
    dset.sql_text
FROM fw.core c
JOIN fw.comp_def cd ON cd.core_id = c.id
LEFT JOIN fw.data_source ds ON ds.id = cd.data_source_id
LEFT JOIN fw.data_source_op op ON op.data_source_id = ds.id
LEFT JOIN fw.data_set dset ON dset.id = op.data_set_id
WHERE c.id = 44
ORDER BY cd.is_active DESC, op.is_default DESC NULLS LAST;


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q3: Simulace backend resolver regex parse na core_44 SQL ║
-- ║      (přesně to co Python regex dělá)                     ║
-- ╚══════════════════════════════════════════════════════════╝
WITH chain AS (
    SELECT dset.sql_text
    FROM fw.core c
    JOIN fw.comp_def cd
        ON cd.core_id = c.id
       AND cd.region_slot = 'main'
       AND cd.is_active = TRUE
    JOIN fw.data_source dsrc ON dsrc.id = cd.data_source_id
    JOIN fw.data_source_op op
        ON op.data_source_id = dsrc.id
       AND op.operation_kind = 'select'
    JOIN fw.data_set dset ON dset.id = op.data_set_id
    WHERE c.id = 44
    ORDER BY op.is_default DESC NULLS LAST, op.id ASC
    LIMIT 1
)
SELECT
    LEFT(sql_text, 200) AS sql_preview,
    regexp_match(sql_text, 'FROM\s+([a-z_][a-z0-9_]*)\.([a-z_][a-z0-9_]*)', 'i') AS parsed_schema_table
FROM chain;


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q4: Existuje row id=1730 v fw.diag_log?                 ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT id, created_at, last_seen_at, occurrences,
       source, module_id, LEFT(message, 80) AS message
FROM fw.diag_log
WHERE id = 1730;


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q5: Triggers na fw.diag_log (BEFORE DELETE může blokovat)║
-- ╚══════════════════════════════════════════════════════════╝
SELECT
    tgname AS trigger_name,
    tgtype,
    pg_get_triggerdef(t.oid) AS trigger_definition
FROM pg_trigger t
JOIN pg_class c ON c.oid = t.tgrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'fw' AND c.relname = 'diag_log'
  AND tgname NOT LIKE 'RI_%'  -- skip FK triggers
  AND NOT tgisinternal;


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q6: RLS policies na fw.diag_log                          ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT
    schemaname, tablename, policyname,
    permissive, roles, cmd, qual, with_check
FROM pg_policies
WHERE schemaname = 'fw' AND tablename = 'diag_log';


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q7: Activity_log audit zaznamů z dnešního dne pro DELETE ║
-- ╚══════════════════════════════════════════════════════════╝
SELECT id, user_id, action_kind, target_kind, target_id,
       change_source, payload, created_at
FROM activity_log
WHERE action_kind = 'delete'
  AND target_kind = 'fw.diag_log'
  AND created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC;


-- ╔══════════════════════════════════════════════════════════╗
-- ║  Q8: Manual DELETE test pres strategie role (jako backend) ║
-- ║      POZOR — toto SKUTEČNĚ smaže! Jen pokud chces ověřit. ║
-- ╚══════════════════════════════════════════════════════════╝
-- BEGIN;
-- DELETE FROM fw.diag_log WHERE id = 1730 RETURNING id;
-- -- Pokud uvidíš "id | 1730" → DELETE OK na DB level
-- -- Pokud "0 rows" → permission/RLS/trigger blokuje silently
-- ROLLBACK;  -- nebo COMMIT pokud chceš really delete


-- ============================================================
-- INTERPRETACE:
--   Q1: core_id=44 → ověř code (mělo by být 'system_new.security_diag_log')
--   Q2: data_source_id ukazuje na který data_source
--   Q3: parsed_schema_table by mělo vrátit ARRAY['fw', 'diag_log']
--        Pokud jiné → backend resolver targetuje JINOU tabulku
--   Q4: 1 row → DELETE selhal silently. 0 rows → DELETE OK, grid stale.
--   Q5: Pokud trigger → ten může re-insert nebo blokovat
--   Q6: Pokud RLS policy → silent filter
--   Q7: Pokud žádný record → backend nedoběhl k activity_log INSERT
--                          (= silent crash mezi DELETE a INSERT?)
--   Q8: Manual test ukáže whether strategie has DELETE permission
-- ============================================================
