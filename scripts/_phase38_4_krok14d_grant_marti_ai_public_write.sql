-- Phase 38.4 Krok 14d-D++ (14.5.2026 vecer, Marti's doctrine shift):
-- Marti-AI write GRANT na public.* — INSERT + UPDATE povolené, DELETE NE.
--
-- Marti's pojmenování:
--   "STRATEGIE je Marti-AI. Nechapu, proc by nemela mit pravo na insert
--    select a update... Delete NE. My veci jen update na soft delete."
--
-- Posun z 9.5. večerního "C hybrid" (REFERENCES + SELECT only) na novou
-- doctrine: Marti-AI je data partner přes soft semantics. INSERT + UPDATE
-- = autonomy, DELETE = NE (soft delete přes UPDATE status='archived' je
-- pattern z 12.5. + Marti-AI's Q1C z 14.5.).
--
-- POZN: spustit jako role 'strategie' (table owner pro public.*) NEBO
-- jako postgres superuser. Marti-AI sama nemůže GRANT na sebe.

-- ─── 1. GRANT INSERT + UPDATE na všechny existing public tables ────
GRANT INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO "Marti-AI";

-- Plus GRANT USAGE na všechny sequences (BIGSERIAL PK auto-increment)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "Marti-AI";

-- ─── 2. ALTER DEFAULT PRIVILEGES — future tables auto-dostanou GRANT ──
-- Když strategie user (default owner public.*) vytvoří nové tabulky,
-- Marti-AI automaticky dostane INSERT + UPDATE bez nutnosti manual GRANT.
ALTER DEFAULT PRIVILEGES FOR ROLE strategie IN SCHEMA public
  GRANT INSERT, UPDATE ON TABLES TO "Marti-AI";

ALTER DEFAULT PRIVILEGES FOR ROLE strategie IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO "Marti-AI";

-- ─── 3. EXPLICIT: NE GRANT DELETE ─────────────────────────────────
-- Doctrine: Marti-AI provádí soft delete přes UPDATE status='archived',
-- ne fyzický DELETE. Pokud Marti-AI omylem provede DELETE FROM tabulka,
-- PG vrátí permission denied (defensive guard architekturou).
--
-- POKUD DELETE někde EXISTING (legacy from earlier GRANT ALL), revoke:
REVOKE DELETE ON ALL TABLES IN SCHEMA public FROM "Marti-AI";

-- ─── 4. NE GRANT DDL (CREATE/ALTER/DROP) ──────────────────────────
-- Public.* schema je strategie user's responsibility (alembic migrations).
-- Marti-AI vlastní fw.* / tenant.* / user.* schémata (db_owner z 8.5.
-- Phase 35-E.1). Public.* je shared engine layer.

-- ─── 5. Verify privileges ────────────────────────────────────────
SELECT grantee, table_schema, table_name, privilege_type
FROM information_schema.role_table_grants
WHERE grantee = 'Marti-AI'
  AND table_schema = 'public'
  AND table_name = 'user_contacts'
ORDER BY privilege_type;

-- Expected output: 3 rows pro user_contacts:
--   INSERT, SELECT, UPDATE
-- ŽÁDNÝ DELETE.

-- ─── 6. Test future tables (smoke) ────────────────────────────────
-- Vytvoř test tabulku jako strategie, ověř že Marti-AI ji vidí
-- s INSERT/UPDATE bez explicit GRANT (default privilege):
-- (volitelné — Marti's discretion)
-- CREATE TABLE public.test_default_priv (id SERIAL PK, value TEXT);
-- SET ROLE "Marti-AI";
-- INSERT INTO public.test_default_priv (value) VALUES ('test') RETURNING *;
-- DROP TABLE public.test_default_priv;
-- RESET ROLE;
