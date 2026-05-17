-- ════════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 14g Etapa F Krok 5.L-D (17.5.2026):
-- ALTER TABLE fw.data_set DROP COLUMN kind
-- ════════════════════════════════════════════════════════════════════════
-- Marti's 17.5. ranní: "Na co se pouziva v datasetu Kind? Neni to matouci?
-- V tom SQL textu muze byt cokoli... Jakakoli kombinace, kterou Kind
-- nereflektuje... Chceme ho na neco?"
--
-- Verdict: data_set.kind je dead weight.
--   - data_source_runner.py runtime filter používá `op.operation_kind`
--     (data_source_op level), NE `ds.kind` (data_set level)
--   - data_set.kind je jen display hint — SQL text může mít CTE pattern
--     (`WITH x AS (UPDATE ...) SELECT * FROM x`) kde kind je nejasný
--   - Drop column je clean break, žádný runtime impact
--
-- ALTER TABLE DROP COLUMN zachová PostgreSQL constraint integrity (kind
-- není FK, není v indexech kromě potenciálních NOT NULL — který Marti
-- nedělal explicit, pojďme).
--
-- Spustit jako Marti-AI v DBeaveru (db_owner fw).
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

ALTER TABLE fw.data_set DROP COLUMN kind;

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY — kind column už neexistuje
-- ════════════════════════════════════════════════════════════════════════
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'fw'
  AND table_name = 'data_set'
ORDER BY ordinal_position;
-- Expected: bez 'kind' column. Existing fields: id, code, sql_text,
-- db_connection, description, is_system, status, created_at...
