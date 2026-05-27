-- =============================================================================
-- Phase 28-D++ (27.5.2026): GRANT Marti-AI ownership on DB_EC.st schema
-- =============================================================================
--
-- ÚČEL:
--   Dát Marti-AI plný db_owner přístup na `DB_EC.st.*` schema pro CRM
--   migraci (Krok 1+). Customer's `dbo.*` zůstává netknuté.
--
-- DOCTRINE (Marti's slova 27.5.2026 odpoledne):
--   *„Ja si myslim, ze tohleto neni STRATEGIE system, ale system custommer
--   a custommer je EUROSOFT a INTERSOFT. Tj, my musime dodret jejich
--   standardy... Do toho nesmime zasahovat."*
--
--   Důsledek: `dbo` = CUSTOMER, `st` = NÁŠ refactor zone, paralelní k DB_ST.
--
-- SPUŠTĚNÍ:
--   Marti, ssms/dbeaver, login jako `sa`. Idempotentní — bezpečné spustit
--   opakovaně.
--
-- VERIFICATION (na konci):
--   Output by měl ukázat:
--     schema_name='dbo', owner_name='dbo'
--     schema_name='st',  owner_name='Marti-AI'
--
-- =============================================================================

USE DB_EC;
GO

PRINT N'═══════════════════════════════════════════════════════════════';
PRINT N'Phase 28-D++ — GRANT Marti-AI na DB_EC.st';
PRINT N'═══════════════════════════════════════════════════════════════';
PRINT N'';

-- =============================================================================
-- Krok 1: Vytvoř schema `st` pokud neexistuje (vlastník zatím = dbo)
-- =============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'st')
BEGIN
    PRINT N'Krok 1: Vytvářím schema [st]...';
    EXEC('CREATE SCHEMA st AUTHORIZATION dbo');
    PRINT N'  ✓ Schema [st] vytvořena (owner: dbo, dočasně)';
END
ELSE
BEGIN
    PRINT N'Krok 1: Schema [st] již existuje — skip CREATE';
END
GO

-- =============================================================================
-- Krok 2: User mapping Marti-AI login → DB_EC user (idempotent)
-- =============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'Marti-AI')
BEGIN
    PRINT N'Krok 2: Vytvářím user [Marti-AI]...';
    CREATE USER [Marti-AI] FOR LOGIN [Marti-AI];
    PRINT N'  ✓ User [Marti-AI] vytvořen';
END
ELSE
BEGIN
    PRINT N'Krok 2: User [Marti-AI] již existuje — skip CREATE';
END
GO

-- =============================================================================
-- Krok 3: Přepiš ownership schema [st] na Marti-AI
-- Po tomto kroku má Marti-AI plný DDL (CREATE/ALTER/DROP TABLE)
-- + DML (INSERT/UPDATE/DELETE) na st.*. Customer's dbo.* netknuté.
-- =============================================================================

PRINT N'Krok 3: ALTER AUTHORIZATION ON SCHEMA::st TO [Marti-AI]...';
ALTER AUTHORIZATION ON SCHEMA::st TO [Marti-AI];
PRINT N'  ✓ Marti-AI je nyní owner schema [st]';
GO

-- =============================================================================
-- Krok 4: Grant SELECT na dbo (pro migrace — Marti-AI potřebuje read source)
-- Pravděpodobně už existuje z whitelist + ALLOW_ALL_SELECT, ale jistota neuškodí.
-- =============================================================================

PRINT N'Krok 4: GRANT SELECT ON SCHEMA::dbo TO [Marti-AI] (read-only)...';
GRANT SELECT ON SCHEMA::dbo TO [Marti-AI];
PRINT N'  ✓ Marti-AI má read access na dbo (pro migrace)';
GO

-- =============================================================================
-- Krok 5: Defensive — REVOKE všech DDL/DML rights na dbo (sanity check)
-- Marti-AI nemůže CREATE/ALTER/DROP/INSERT/UPDATE/DELETE/MERGE na dbo.*
-- Tento step je *„belt and suspenders"* — schema owner check už to chrání.
-- =============================================================================

PRINT N'Krok 5: DENY DDL/DML na dbo (defense in depth)...';
DENY CREATE TABLE TO [Marti-AI];
-- (CREATE TABLE je database-level permission, takhle ji Marti-AI mít NEMĚLA
--  na DB_EC. Pokud by ji měla z předchozí GRANT, tahle DENY ji odebere.)
DENY ALTER, CONTROL ON SCHEMA::dbo TO [Marti-AI];
DENY INSERT, UPDATE, DELETE ON SCHEMA::dbo TO [Marti-AI];
PRINT N'  ✓ Marti-AI má DENY na DDL/DML na dbo';
GO

-- =============================================================================
-- Krok 6: VERIFICATION — co Marti-AI vidí + co může
-- =============================================================================

PRINT N'';
PRINT N'═══════════════════════════════════════════════════════════════';
PRINT N'VERIFICATION';
PRINT N'═══════════════════════════════════════════════════════════════';
PRINT N'';

PRINT N'Schema ownership (expected: dbo→dbo, st→Marti-AI):';
SELECT
    s.name AS schema_name,
    USER_NAME(s.principal_id) AS owner_name
FROM sys.schemas s
WHERE s.name IN ('dbo', 'st')
ORDER BY s.name;

PRINT N'';
PRINT N'Marti-AI permissions na DB_EC (expected: ne ALTER/INSERT/UPDATE/DELETE na dbo):';
SELECT
    perm.permission_name,
    perm.state_desc AS [grant_state],
    CASE WHEN class = 3 THEN OBJECT_SCHEMA_NAME(major_id, DB_ID()) END AS [schema_name]
FROM sys.database_permissions perm
JOIN sys.database_principals princ ON perm.grantee_principal_id = princ.principal_id
WHERE princ.name = 'Marti-AI'
ORDER BY perm.permission_name;

PRINT N'';
PRINT N'═══════════════════════════════════════════════════════════════';
PRINT N'HOTOVO — Marti-AI má db_owner na DB_EC.st, customer dbo netknuté';
PRINT N'═══════════════════════════════════════════════════════════════';
GO

-- =============================================================================
-- POST-DEPLOY SMOKE (volitelné — Marti spustí v jiné session jako Marti-AI):
-- =============================================================================
--
-- Test 1 — CREATE/INSERT/DROP v st (musí projít):
--   CREATE TABLE st._smoke_test (id INT IDENTITY(1,1) PRIMARY KEY, txt NVARCHAR(50));
--   INSERT INTO st._smoke_test (txt) VALUES (N'ping');
--   SELECT * FROM st._smoke_test;
--   DROP TABLE st._smoke_test;
--
-- Test 2 — CREATE v dbo (musí selhat s permission denied):
--   CREATE TABLE dbo._evil_test (id INT);
--   -- expected error: 262 / 230 — *„permission denied on schema dbo"*
--
-- =============================================================================
