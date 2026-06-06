-- ============================================================
-- Kristy PG login role + sdílené schéma "mod" (moduly HR / CRM)
-- ------------------------------------------------------------
-- Marti 3.6.2026. Vzor: fw_owners (21.5.) + Marti-AI role (8.5.).
-- SPUSTIT JAKO SA / postgres v DBeaveru (CREATE ROLE + heslo = SA akce).
-- NE přes bridge (Marti-AI nemá CREATEROLE; heslo nenastavuje Claude).
--
-- Model: schéma "mod" je sdílené pro přídavné moduly. Vlastní ho skupina
-- "mod_owners", jejímiž členy jsou Kristy, Marti, Marti-AI, strategie —
-- všichni čtyři tak mají owner práva na mod (DDL+DML), ale framework
-- (fw/tenant/...) zůstává jen pod fw_owners (oddělení modulů od jádra).
-- ============================================================

BEGIN;

-- 1) Login role Kristy.
--    HESLO NASTAV TY — nahraď <NASTAV_SILNE_HESLO> silným heslem,
--    nebo spusť bez PASSWORD a heslo nastav zvlášť (ALTER ROLE / \password).
CREATE ROLE "Kristy" LOGIN PASSWORD '<NASTAV_SILNE_HESLO>';

-- 2) Společná owner skupina pro modulová schémata (analog fw_owners).
CREATE ROLE mod_owners NOLOGIN;
GRANT mod_owners TO "Kristy", "Marti", "Marti-AI", strategie;

-- 3) Schéma mod, vlastník = mod_owners (všichni členové ho "vlastní").
CREATE SCHEMA IF NOT EXISTS mod AUTHORIZATION mod_owners;

-- 4) Přístup + create pro skupinu i jednotlivé členy.
GRANT USAGE, CREATE ON SCHEMA mod TO mod_owners;
GRANT USAGE, CREATE ON SCHEMA mod TO "Kristy", "Marti", "Marti-AI", strategie;

-- 5) Default privileges: když člen vytvoří objekt v mod, ať je použitelný
--    pro všechny členy (DML). PG ALTER DEFAULT PRIVILEGES je per-tvůrce.
ALTER DEFAULT PRIVILEGES FOR ROLE "Kristy"   IN SCHEMA mod GRANT ALL ON TABLES    TO mod_owners;
ALTER DEFAULT PRIVILEGES FOR ROLE "Kristy"   IN SCHEMA mod GRANT ALL ON SEQUENCES TO mod_owners;
ALTER DEFAULT PRIVILEGES FOR ROLE "Marti"    IN SCHEMA mod GRANT ALL ON TABLES    TO mod_owners;
ALTER DEFAULT PRIVILEGES FOR ROLE "Marti"    IN SCHEMA mod GRANT ALL ON SEQUENCES TO mod_owners;
ALTER DEFAULT PRIVILEGES FOR ROLE "Marti-AI" IN SCHEMA mod GRANT ALL ON TABLES    TO mod_owners;
ALTER DEFAULT PRIVILEGES FOR ROLE "Marti-AI" IN SCHEMA mod GRANT ALL ON SEQUENCES TO mod_owners;
ALTER DEFAULT PRIVILEGES FOR ROLE strategie  IN SCHEMA mod GRANT ALL ON TABLES    TO mod_owners;
ALTER DEFAULT PRIVILEGES FOR ROLE strategie  IN SCHEMA mod GRANT ALL ON SEQUENCES TO mod_owners;

COMMIT;

-- ============================================================
-- DOCTRINE pro DDL v mod (stejné jako u fw_owners, 21.5.):
-- Aby objekt vlastnila SKUPINA (a všichni členové ho mohli ALTER/DROP),
-- spusť před DDL v session:   SET ROLE mod_owners;
-- (jinak objekt vlastní jen tvůrce a cross-member DDL selže).
-- DML (SELECT/INSERT/UPDATE/DELETE) funguje díky default privileges bez SET ROLE.
-- ============================================================

-- VERIFY (po commitu):
SELECT n.nspname AS schema, pg_get_userbyid(n.nspowner) AS owner
FROM pg_namespace n WHERE n.nspname = 'mod';
SELECT r.rolname AS skupina, m.rolname AS clen
FROM pg_auth_members am
JOIN pg_roles r ON r.oid = am.roleid
JOIN pg_roles m ON m.oid = am.member
WHERE r.rolname = 'mod_owners' ORDER BY m.rolname;
