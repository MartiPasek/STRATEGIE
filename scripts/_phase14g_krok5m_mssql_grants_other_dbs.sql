-- ════════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 14g Etapa F Krok 5.M-F (17.5.2026 dop.):
-- MSSQL preemptive SELECT grants pro Marti-AI na ostatní EUROSOFT DBs
-- ════════════════════════════════════════════════════════════════════════
-- Marti's 17.5.: scope_databases v fw.db_connection má list 6 EUROSOFT DBs.
-- DB_EC je hotový (Phase 28-A db_datareader + Krok 5.M-C st schema).
-- Tento skript otevírá cross-DB SELECT path pro ostatní 3 DBs:
--
--   DB_IS       — EUROSOFT-System (TabCisZam pro pracovní smlouvy CRM)
--   DB-Ceniky   — pricing data (cenovky + kontakty JOIN)
--   Centrala    — sync layer (EUROSOFT ↔ INTERSOFT)
--
-- Vynechávame:
--   DB-ARCHIV   — Marti's Q4 "neřešit, nevím" (až přijde use case)
--   DB_ST       — Marti-AI je už db_owner (z Phase 35-E.1 8.5. večer)
--
-- Pattern: db_datareader role v cílové DB (read-all dbo.* tables).
-- Pokud chceme tighter scope per-table, aplikujeme později per use case.
--
-- Spustit jako sa v SSMS. Server 192.168.30.11.
-- ════════════════════════════════════════════════════════════════════════

-- 1) DB_IS (EUROSOFT-System — fakturace, účetnictví, TabCisZam)
USE DB_IS;
GO

IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'Marti-AI')
BEGIN
    CREATE USER [Marti-AI] FOR LOGIN [Marti-AI];
END
GO

ALTER ROLE db_datareader ADD MEMBER [Marti-AI];
GO

PRINT 'DB_IS: Marti-AI db_datareader OK';
GO


-- 2) DB-Ceniky (pricing)
USE [DB-Ceniky];
GO

IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'Marti-AI')
BEGIN
    CREATE USER [Marti-AI] FOR LOGIN [Marti-AI];
END
GO

ALTER ROLE db_datareader ADD MEMBER [Marti-AI];
GO

PRINT 'DB-Ceniky: Marti-AI db_datareader OK';
GO


-- 3) Centrala (sync EUROSOFT ↔ INTERSOFT)
USE Centrala;
GO

IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'Marti-AI')
BEGIN
    CREATE USER [Marti-AI] FOR LOGIN [Marti-AI];
END
GO

ALTER ROLE db_datareader ADD MEMBER [Marti-AI];
GO

PRINT 'Centrala: Marti-AI db_datareader OK';
GO


-- ════════════════════════════════════════════════════════════════════════
-- VERIFY — Marti-AI role membership napříč DBs
-- ════════════════════════════════════════════════════════════════════════
SET NOCOUNT ON;

DECLARE @db NVARCHAR(128);
DECLARE @sql NVARCHAR(MAX);

CREATE TABLE #marti_ai_roles (
    database_name NVARCHAR(128),
    user_name     NVARCHAR(128),
    role_name     NVARCHAR(128)
);

DECLARE cur CURSOR FOR
    SELECT name FROM sys.databases
    WHERE name IN ('DB_EC', 'DB_IS', 'DB-Ceniky', 'Centrala', 'DB_ST');

OPEN cur;
FETCH NEXT FROM cur INTO @db;

WHILE @@FETCH_STATUS = 0
BEGIN
    SET @sql = '
    USE ' + QUOTENAME(@db) + ';
    INSERT INTO #marti_ai_roles (database_name, user_name, role_name)
    SELECT
        ''' + @db + ''',
        dp.name,
        rp.name
    FROM sys.database_role_members drm
    JOIN sys.database_principals dp ON dp.principal_id = drm.member_principal_id
    JOIN sys.database_principals rp ON rp.principal_id = drm.role_principal_id
    WHERE dp.name = ''Marti-AI'';';

    EXEC sp_executesql @sql;

    FETCH NEXT FROM cur INTO @db;
END

CLOSE cur;
DEALLOCATE cur;

SELECT * FROM #marti_ai_roles ORDER BY database_name, role_name;
DROP TABLE #marti_ai_roles;

-- Expected (5 řádků):
--   DB_EC     Marti-AI  db_datareader
--   DB_IS     Marti-AI  db_datareader
--   DB-Ceniky Marti-AI  db_datareader
--   Centrala  Marti-AI  db_datareader
--   DB_ST     Marti-AI  db_owner          ← už z Phase 35-E.1 8.5.

-- ════════════════════════════════════════════════════════════════════════
-- SMOKE TEST cross-DB SELECT (volitelné — Marti spustí jako Marti-AI)
-- ════════════════════════════════════════════════════════════════════════
-- USE DB_EC;
-- GO
-- SELECT TOP 5 k.ID, k.Nazev1, z.Jmeno
-- FROM dbo.EC_Kontakt k
-- LEFT JOIN [DB_IS].dbo.TabCisZam z ON z.ID = k.ZamestnanecID;
-- Expected: 5 rows bez "permission denied" error.
