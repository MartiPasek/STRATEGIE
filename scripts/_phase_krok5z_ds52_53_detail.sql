-- ============================================================================
-- Krok 5.Z (31.5.2026) — Detail data_source 52 (Akce) + 53 (Osoby) pro core
-- ============================================================================
-- Audit ukazal 2 nested gridy v core 72:
--   373 -> ds 52 crm_kontakt_akce_detail
--   372 -> ds 53 crm_kontakt_osoby_detail
-- Oba maji data_set_id NULL v select-join -> potrebuju videt VSECHNY ops a
-- skutecny SQL, hlavne jak resi filtr :master_id (kvuli standalone master).
--
-- READ-ONLY. Spusti Marti v DBeaveru.
-- ============================================================================

-- ── 1) data_source hlavicky ─────────────────────────────────────────────────
SELECT id, code, name, refresh_type, status, is_system
FROM fw.data_source
WHERE id IN (52, 53)
ORDER BY id;

-- ── 2) VSECHNY ops (jakykoliv kind) + jejich data_set + plny SQL ────────────
SELECT
    op.id                AS op_id,
    op.data_source_id,
    op.operation_kind,
    op.variant_code,
    op.is_default,
    op.core_id           AS op_core_id,
    op.data_set_id,
    dset.code            AS data_set_code,
    dset.db_connection_id,
    dset.sql_text        AS full_sql
FROM fw.data_source_op op
LEFT JOIN fw.data_set dset ON dset.id = op.data_set_id
WHERE op.data_source_id IN (52, 53)
ORDER BY op.data_source_id, op.is_default DESC NULLS LAST, op.id;

-- ============================================================================
-- Co z toho potřebuju:
--   - Plný SELECT text (full_sql) obou data_sources.
--   - Jak je filtr :master_id v SQL napsaný:
--       a) tvrdě: WHERE IDHlav = :master_id   -> standalone master = prázdný
--          => upravit na: WHERE (:master_id IS NULL OR IDHlav = :master_id)
--       b) už optional / parametrizovaný -> reuse beze změny
--   - operation_kind (select? list? jiný variant?) — abych v creation scriptu
--     navázal grid root na správný op.
-- ============================================================================
