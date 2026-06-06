-- ============================================================================
-- Vrstva 1 hardening — DB timeouty (Marti 3.6.2026, po incidentu se zaseklým ALTER)
-- ============================================================================
-- Spustit JAKO SA (postgres superuser) v DBeaveru na cloud SQL (10.200.188.12).
--
-- Co to dělá:
--   statement_timeout = strop na DÉLKU jakéhokoli dotazu (po limitu PG zabije)
--   lock_timeout      = strop na ČEKÁNÍ na zámek (po limitu dotaz vzdá zámek)
--
-- Proč: dnešní incident = ALTER čekal NEKONEČNĚ na zámek horké tabulky →
--   fronta zámků → API nenaběhlo. S lock_timeout by ALTER po 5 s vzdal a
--   všechno jelo dál. Tohle je pojistka, aby ŽÁDNÝ dotaz/DDL nemohl viset
--   donekonečna a strhnout API — DB se sama uzdraví.
--
-- Dědí KAŽDÉ nové připojení. Existující spojení se obnoví restartem API
-- (Restart-Service STRATEGIE-API) — provede se mimo špičku.
--
-- Pozn.: PG statement_timeout NEovlivňuje MSSQL/MCP volání (jiné spojení) —
--   ta mají vlastní 10s/30s timeout (řešeno dřív).
-- ============================================================================

-- App role (běžné dotazy, grids, CRUD)
ALTER ROLE strategie  SET statement_timeout = '60s';
ALTER ROLE strategie  SET lock_timeout      = '5s';

-- Marti-AI role (bridge write-approval + DDL přes strategie_pg engine)
ALTER ROLE "Marti-AI" SET statement_timeout = '60s';
ALTER ROLE "Marti-AI" SET lock_timeout      = '5s';

-- Kristy role (až bude přes ni něco jezdit)
ALTER ROLE "Kristy"   SET statement_timeout = '60s';
ALTER ROLE "Kristy"   SET lock_timeout      = '5s';

-- DB-level fallback (kdyby přibyla další role bez nastavení)
ALTER DATABASE data_db SET lock_timeout = '5s';

-- ── Ověření (spusť po nastavení) ───────────────────────────────────────────
-- SELECT rolname,
--        (SELECT option_value FROM pg_options_to_table(rolconfig)
--         WHERE option_name='statement_timeout') AS stmt_to,
--        (SELECT option_value FROM pg_options_to_table(rolconfig)
--         WHERE option_name='lock_timeout') AS lock_to
-- FROM pg_roles WHERE rolname IN ('strategie','Marti-AI','Kristy');
