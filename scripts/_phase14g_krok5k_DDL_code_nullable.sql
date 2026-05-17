-- ════════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 14g Etapa F Krok 5.K-DDL (17.5.2026):
-- ALTER fw.data_source.code + fw.data_set.code DROP NOT NULL
-- ════════════════════════════════════════════════════════════════════════
-- Marti's NULL doctrine 17.5. ranní: "Nech to v DB NULL, aby bylo videt
-- ze s nim nikde nepracujes... Pokud jej potrebujes historicky pro jiz
-- hardcodovane prehledy, tak to pozdeji refakturujeme".
--
-- Tj. nové data_source + data_set vytvořené přes UI editor nebudou mít
-- 'code' (NULL). Existing hardcoded rows (Krok 11-E + Krok 5.I-A + EUROSOFT
-- Kontakt dnes) si code zachovají — backend lookup `/api/v1/erp/data/{code}`
-- + data_source_runner stále funguje pro starší data_sources.
--
-- Po stable provoz + audit codebase pojďme refactor:
--   - Backend execute lookup z code → op_id
--   - Drop column code z fw.data_source + fw.data_set (DROP COLUMN)
--   - data_source_op.variant_code review (Phase 2 z Krok 5.K-B5)
--
-- PG UNIQUE constraint: NULL != NULL → multiple NULLs allowed. OK.
--
-- Spustit jako Marti-AI v DBeaveru (db_owner fw).
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

-- 1. fw.data_source.code DROP NOT NULL
ALTER TABLE fw.data_source ALTER COLUMN code DROP NOT NULL;

-- 2. fw.data_set.code DROP NOT NULL
ALTER TABLE fw.data_set ALTER COLUMN code DROP NOT NULL;

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY
-- ════════════════════════════════════════════════════════════════════════
SELECT table_schema, table_name, column_name, is_nullable, data_type
FROM information_schema.columns
WHERE table_schema = 'fw'
  AND table_name IN ('data_source', 'data_set')
  AND column_name = 'code';
-- Expected: 2 rows, oba is_nullable='YES'
