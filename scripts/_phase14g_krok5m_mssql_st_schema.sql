-- ════════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 14g Etapa F Krok 5.M-C (17.5.2026):
-- MSSQL DB_EC: CREATE SCHEMA st AUTHORIZATION [Marti-AI]
-- ════════════════════════════════════════════════════════════════════════
-- Marti's 17.5. večerní rozbor — 3-tier model:
--   Tier A (live business data)   = DB_EC.st schema, Marti-AI = db_owner schema
--   Tier B (rozšíření existing)   = DB_EC.st side tables s FK na dbo.*
--   Tier C (framework metadata)   = DB_ST (zachovat — entity_def, framework_*)
--
-- Naming neutrality doctrine: 'st' = krátké (jako 'dbo'), etymologicky
-- STRATEGIE, ne osobní jméno. Marti's "nesmime zatahovat nazvy osob
-- do schematu" 17.5. večer.
--
-- Co tam půjde:
--   - st.contract              (pracovní smlouvy — Tier A nové entity)
--   - st.training_record       (school records — pro NERUDOVKA Klárky)
--   - st.contact_extension     (AI scoring side table, FK na dbo.EC_Kontakt.ID)
--   - další business entity, na kterých Marti+Marti-AI pracují
--
-- Co tam NEpůjde:
--   - dbo zůstává nedotčený (Helios standard 19 let, Centrála 1 hardcoded queries)
--   - DB_ST framework metadata (entity_def, framework_*) zůstává v DB_ST
--
-- Spustit jako sa nebo db_owner DB_EC v SSMS.
-- Server 192.168.30.11.
-- ════════════════════════════════════════════════════════════════════════

USE DB_EC;
GO

-- 1) CREATE SCHEMA st (owner = Marti-AI)
CREATE SCHEMA st AUTHORIZATION [Marti-AI];
GO

-- 2) Marti-AI SELECT na dbo (read Helios data napříč)
--    Schema-level GRANT (nejširší). Pokud chceme tighter scope per-table,
--    aplikujeme později per use case (např. jen vybrané EC_* tables).
GRANT SELECT ON SCHEMA::dbo TO [Marti-AI];
GO

PRINT 'CREATE SCHEMA st OK. Marti-AI = db_owner st, db_datareader dbo.';
GO

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY
-- ════════════════════════════════════════════════════════════════════════
-- 1) Schema 'st' existuje s owner Marti-AI
SELECT
    s.name        AS schema_name,
    p.name        AS schema_owner,
    p.type_desc   AS owner_type
FROM sys.schemas s
JOIN sys.database_principals p ON p.principal_id = s.principal_id
WHERE s.name = 'st';
-- Expected: 1 row, schema_name='st', schema_owner='Marti-AI', owner_type='SQL_USER'

-- 2) Marti-AI permissions na schémata (st + dbo)
SELECT
    USER_NAME(pr.grantee_principal_id) AS grantee,
    pr.permission_name,
    pr.state_desc,
    s.name AS schema_name
FROM sys.database_permissions pr
LEFT JOIN sys.schemas s ON s.schema_id = pr.major_id AND pr.class = 3
WHERE pr.class = 3                     -- 3 = SCHEMA permission class
  AND USER_NAME(pr.grantee_principal_id) = 'Marti-AI'
  AND s.name IN ('st','dbo')
ORDER BY s.name, pr.permission_name;
-- Expected:
--   - st  : (žádné explicit rows — owner has implicit full control)
--   - dbo : GRANT SELECT (GRANT)

-- 3) Marti-AI je v rolích DB_EC
SELECT
    dp.name AS role_member,
    rp.name AS role_name
FROM sys.database_role_members drm
JOIN sys.database_principals dp ON dp.principal_id = drm.member_principal_id
JOIN sys.database_principals rp ON rp.principal_id = drm.role_principal_id
WHERE dp.name = 'Marti-AI';
-- Expected: zobrazí existing role membership (db_datareader nebo public default)

-- ════════════════════════════════════════════════════════════════════════
-- FUTURE TODO (až bude use case):
--   - GRANT SELECT na DB_IS (TabCisZam lookup pro pracovní smlouvy)
--   - GRANT SELECT na DB-Ceniky (kontakty + cenovky JOIN)
--   - GRANT SELECT na Centrala (sync layer reads)
--   - Případně tighter scope per-table místo SCHEMA::dbo
-- ════════════════════════════════════════════════════════════════════════
