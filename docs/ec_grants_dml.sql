/* =====================================================================
   DB_EC — hromadný GRANT INSERT/UPDATE loginu [Marti-AI] (MCP STRATEGIE)
   ---------------------------------------------------------------------
   Účel (Marti 19.6.2026): rychlé ladění produkce — STRATEGIE smí přes
   EUROSOFT MCP zapisovat (INSERT/UPDATE) do tabulek DB_EC. DELETE se
   přidá AŽ později (řádek je připravený, zatím zakomentovaný).

   POZOR — toto je změna OPRÁVNĚNÍ na produkčním MSSQL (DB_EC = zákaznická
   doména Centrály). Spouští DBA / sysadmin EUROSOFTu, NE STRATEGIE bridge.
   Login [Marti-AI] sám si práva udělit nemůže (je db_datareader).

   Instance: 192.168.30.11\SQLEXPRESS2017   ·   DB: DB_EC
   Login:    Marti-AI  (EUROSOFT_SQL_USER)
   ===================================================================== */

USE [DB_EC];
GO

/* --- DOPORUČENO: schema-level grant = pokryje všechny SOUČASNÉ i BUDOUCÍ
   tabulky/pohledy ve schématu dbo (není třeba opakovat po přidání tabulky). */
GRANT INSERT, UPDATE ON SCHEMA::dbo TO [Marti-AI];
GO

/* DELETE — ZATÍM NE. Odkomentovat, až bude potřeba (Marti: „později i delete"). */
-- GRANT DELETE ON SCHEMA::dbo TO [Marti-AI];
-- GO

/* =====================================================================
   ALTERNATIVA (kdyby DBA nechtěl schema-level): per-tabulka jen BASE TABLES.
   Vygeneruje a rovnou spustí GRANT INSERT,UPDATE na každou dbo tabulku.
   ---------------------------------------------------------------------
DECLARE @sql nvarchar(max) = N'';
SELECT @sql = @sql + N'GRANT INSERT, UPDATE ON ' + QUOTENAME(s.name) + N'.' + QUOTENAME(t.name) + N' TO [Marti-AI];' + CHAR(13)
FROM sys.tables t JOIN sys.schemas s ON s.schema_id = t.schema_id
WHERE s.name = 'dbo';
EXEC sp_executesql @sql;
   ===================================================================== */

/* --- Ověření udělených práv loginu [Marti-AI] na DB_EC: */
SELECT pr.permission_name, pr.state_desc,
       COALESCE(OBJECT_SCHEMA_NAME(pr.major_id) + '.' + OBJECT_NAME(pr.major_id), 'SCHEMA::dbo') AS na_objektu
FROM sys.database_permissions pr
JOIN sys.database_principals dp ON dp.principal_id = pr.grantee_principal_id
WHERE dp.name = 'Marti-AI' AND pr.permission_name IN ('INSERT','UPDATE','DELETE')
ORDER BY pr.permission_name;
GO
