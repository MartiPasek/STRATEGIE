/* ============================================================================
   Přidání účetních uživatelů do MSSQL — cloud Helios
   Server:   EUR-DB-MSSQL-1P  (10.200.188.12)
   Databáze: UCTO_EC, UCTO_ES  (účetnictví Helios)
   Autentizace: SQL login (stejně jako stávající připojení přes 'sa').

   NÁVOD:
     1) Otevři v SSMS připojený k EUR-DB-MSSQL-1P jako 'sa' (nebo admin).
     2) Nahraď  <HESLO_MARTIA>  a  <HESLO_PETA>  vlastními SILNÝMI hesly
        (ulož je do Bitwarden — internet-facing brána, mzdy/účto).
     3) Spusť celý skript (F5). Na konci uvidíš kontrolní výpis.
     4) V Heliosu každé účetní nastav připojení: SQL login Martia / Peta + heslo.

   Pozn.: SQL loginy jsou case-insensitive (Martia == martia).
          Helios pro plnou funkci vyžaduje roli db_owner na své DB.
   ============================================================================ */

USE [master];
GO

/* --- 1) SERVER LOGINY (SQL autentizace) --------------------------------- */
IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = N'Martia')
    CREATE LOGIN [Martia] WITH PASSWORD = N'<HESLO_MARTIA>',
        DEFAULT_DATABASE = [UCTO_EC], CHECK_POLICY = ON;
GO
IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = N'Peta')
    CREATE LOGIN [Peta] WITH PASSWORD = N'<HESLO_PETA>',
        DEFAULT_DATABASE = [UCTO_EC], CHECK_POLICY = ON;
GO

/* --- 2) UCTO_EC — uživatelé + role (Helios potřebuje db_owner) ---------- */
USE [UCTO_EC];
GO
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'Martia')
    CREATE USER [Martia] FOR LOGIN [Martia];
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'Peta')
    CREATE USER [Peta] FOR LOGIN [Peta];
ALTER ROLE [db_owner] ADD MEMBER [Martia];
ALTER ROLE [db_owner] ADD MEMBER [Peta];
GO

/* --- 3) UCTO_ES — totéž ------------------------------------------------- */
USE [UCTO_ES];
GO
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'Martia')
    CREATE USER [Martia] FOR LOGIN [Martia];
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'Peta')
    CREATE USER [Peta] FOR LOGIN [Peta];
ALTER ROLE [db_owner] ADD MEMBER [Martia];
ALTER ROLE [db_owner] ADD MEMBER [Peta];
GO

/* --- 4) KONTROLA -------------------------------------------------------- */
SELECT DB_NAME() AS databaze, dp.name AS uzivatel, r.name AS role
FROM sys.database_role_members drm
JOIN sys.database_principals dp ON dp.principal_id = drm.member_principal_id
JOIN sys.database_principals r  ON r.principal_id  = drm.role_principal_id
WHERE dp.name IN (N'Martia', N'Peta');
GO
