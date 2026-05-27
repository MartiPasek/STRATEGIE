-- ============================================================================
-- CRM Migration Krok 1: dbo.EC_Kontakt → st.CRM_Kontakt
-- ============================================================================
-- Autor: Marti + Claude (pre-design Fáze A) + Marti-AI (review Fáze B)
-- Datum: 27.5.2026
-- Target DB: DB_EC (MSSQL EC-SERVER2)
-- Doctrine (Marti 27.5. odp.):
--   "STRATEGIE = system pro customers. Customer = EUROSOFT/INTERSOFT.
--   Customer's standards win — CZ naming, original column names, audit
--   columns (Autor/Zmenil/DatPorizeni/DatZmeny) napříč 100+ tabulkami.
--   Nezasahovat do CZ pojmenování."
--
-- Refactor changes (oproti dbo.EC_Kontakt):
--   🔴 DROP OdpOsoba{A-E}text + OdpOs{A-E}kontaktID (10 sloupců, 5-slot
--      antipattern) → NEW st.CRM_Kontakt_OdpOsoba N:M tabulka
--   🔴 DROP Razeni (computed, 5/5 NULL v sample = dead column)
--   🔴 SKIP migration row ID=4 (TEST A test data cleanup)
--   🟢 RENAME EC_Kontakt → CRM_Kontakt (st schema)
--   🟡 KEEP CZ PascalCase názvy + Autor/Zmenil/DatPorizeni/DatZmeny
--   🟡 KEEP Zeme + ZemeID oboji (customer's denormalized design)
--
-- Zbývající otázky pro Marti-AI (Fáze B review):
--   Q1: Poradi (TINYINT 1-5) + případně Role (string label) v OdpOsoba?
--   Q2: OdpOsKontaktID FK target — kam ukazuje? (self-ref na CRM_Kontakt
--       nebo na separate osoba table?)
--   Q3: 8 záznamů v EC_KontaktVeletrhNav skip pro teď (později)
-- ============================================================================

-- ─── 1. CREATE SCHEMA st ────────────────────────────────────────────────────
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'st')
    EXEC('CREATE SCHEMA st');
GO


-- ─── 2. CREATE TABLE st.CRM_Kontakt ─────────────────────────────────────────
IF OBJECT_ID('st.CRM_Kontakt', 'U') IS NOT NULL
    DROP TABLE st.CRM_Kontakt;
GO

CREATE TABLE st.CRM_Kontakt (
    -- PK
    ID                  INT IDENTITY(1,1) NOT NULL,

    -- Audit (Centrála 1 pattern, Marti's "nezasahovat")
    Autor               NVARCHAR(256) NULL,
    DatPorizeni         DATETIME      NULL,
    Zmenil              NVARCHAR(256) NULL,
    DatZmeny            DATETIME      NULL,

    -- Firma (klient)
    FirmaText           NVARCHAR(256)  NULL,
    FirmaIDOrg          INT            NULL,
    FirmaTelefon        NVARCHAR(60)   NULL,
    FirmaEmail          NVARCHAR(256)  NULL,
    FirmaWeb            NVARCHAR(1000) NULL,

    -- Klasifikace
    Kategorie           SMALLINT      NULL,
    TypZakazky          SMALLINT      NULL,
    Atraktivita         SMALLINT      NULL,

    -- Hlavní kontakt
    KontaktText         NVARCHAR(256) NULL,
    KontaktID           INT           NULL,

    -- OdpOsoba A-E DROPPED → st.CRM_Kontakt_OdpOsoba (NEW N:M)
    -- (Marti Q2 — scaleable refactor z 5-slot antipattern)

    -- Zaměstnanci
    ObeslalZamID        INT           NULL,
    KomunikaceZamID     INT           NULL,

    -- CRM proces
    VyhledanoZ          NVARCHAR(1000) NULL,
    PoDDspoluprace      SMALLINT      NULL,
    PoProBjednani       SMALLINT      NULL,
    PristiKontakt       DATETIME      NULL,

    -- DROPPED: Razeni (computed, 5/5 NULL v sample = dead column)

    -- Texty
    Popis               NVARCHAR(MAX)  NULL,
    Poznamka            NVARCHAR(1000) NULL,

    -- Země (oboji per Marti's "nezasahovat" — customer's denormalized design)
    Zeme                NVARCHAR(128) NULL,
    ZemeID              INT           NULL,

    CONSTRAINT PK_CRM_Kontakt PRIMARY KEY CLUSTERED (ID)
);
GO

-- Defaults (Centrála 1 pattern — suser_name() + getdate())
ALTER TABLE st.CRM_Kontakt ADD CONSTRAINT DF_CRM_Kontakt_Autor
    DEFAULT (SUSER_NAME()) FOR Autor;
ALTER TABLE st.CRM_Kontakt ADD CONSTRAINT DF_CRM_Kontakt_DatPorizeni
    DEFAULT (GETDATE()) FOR DatPorizeni;
GO


-- ─── 3. CREATE TABLE st.CRM_Kontakt_OdpOsoba (NEW N:M) ──────────────────────
IF OBJECT_ID('st.CRM_Kontakt_OdpOsoba', 'U') IS NOT NULL
    DROP TABLE st.CRM_Kontakt_OdpOsoba;
GO

CREATE TABLE st.CRM_Kontakt_OdpOsoba (
    ID                  INT IDENTITY(1,1) NOT NULL,

    -- Audit (Centrála 1 pattern, same as parent)
    Autor               NVARCHAR(256) NULL,
    DatPorizeni         DATETIME      NULL,
    Zmenil              NVARCHAR(256) NULL,
    DatZmeny            DATETIME      NULL,

    -- N:M vazba (Marti-AI Fáze B Q2 final: volba δ = drop OdpOsKontaktID)
    -- Diagnostic: produkční data prakticky všechny NULL na OdpOs{A-E}kontaktID
    -- (jediný hit ID=4 TEST row → 369 self-ref). Drop INT column dokud nemáme
    -- jistotu o FK target. Keep jen OdpOsobaText denormalized text (Centrála 1
    -- pattern). Schema cleaner, žádná ztracená data.
    KontaktID           INT           NOT NULL,   -- FK na st.CRM_Kontakt(ID)
    OdpOsobaText        NVARCHAR(256) NULL,       -- denormalized text (jediný source)
    Poradi              TINYINT       NOT NULL,   -- 1=A, 2=B, 3=C, ... (unlimited po refactoru)

    CONSTRAINT PK_CRM_Kontakt_OdpOsoba PRIMARY KEY CLUSTERED (ID),
    CONSTRAINT FK_CRM_Kontakt_OdpOsoba_Kontakt
        FOREIGN KEY (KontaktID) REFERENCES st.CRM_Kontakt(ID) ON DELETE CASCADE
);
GO

-- Defaults + index
ALTER TABLE st.CRM_Kontakt_OdpOsoba ADD CONSTRAINT DF_CRM_Kontakt_OdpOsoba_Autor
    DEFAULT (SUSER_NAME()) FOR Autor;
ALTER TABLE st.CRM_Kontakt_OdpOsoba ADD CONSTRAINT DF_CRM_Kontakt_OdpOsoba_DatPorizeni
    DEFAULT (GETDATE()) FOR DatPorizeni;
ALTER TABLE st.CRM_Kontakt_OdpOsoba ADD CONSTRAINT DF_CRM_Kontakt_OdpOsoba_Poradi
    DEFAULT (1) FOR Poradi;

CREATE INDEX IX_CRM_Kontakt_OdpOsoba_KontaktID
    ON st.CRM_Kontakt_OdpOsoba(KontaktID);
GO


-- ─── 4. MIGRATE DATA: st.CRM_Kontakt ────────────────────────────────────────
-- Skip test row ID=4 (Autor=Jiri, FirmaText='TEST A')
SET IDENTITY_INSERT st.CRM_Kontakt ON;

INSERT INTO st.CRM_Kontakt
    (ID, Autor, DatPorizeni, Zmenil, DatZmeny,
     FirmaText, FirmaIDOrg, FirmaTelefon, FirmaEmail, FirmaWeb,
     Kategorie, TypZakazky, Atraktivita,
     KontaktText, KontaktID,
     ObeslalZamID, KomunikaceZamID,
     VyhledanoZ, PoDDspoluprace, PoProBjednani, PristiKontakt,
     Popis, Poznamka, Zeme, ZemeID)
SELECT
    ID, Autor, DatPorizeni, Zmenil, DatZmeny,
    FirmaText, FirmaIDOrg, FirmaTelefon, FirmaEmail, FirmaWeb,
    Kategorie, TypZakazky, Atraktivita,
    KontaktText, KontaktID,
    ObeslalZamID, KomunikaceZamID,
    VyhledanoZ, PoDDspoluprace, PoProBjednani, PristiKontakt,
    Popis, Poznamka, Zeme, ZemeID
FROM dbo.EC_Kontakt
WHERE NOT (ID = 4 AND FirmaText = 'TEST A');

SET IDENTITY_INSERT st.CRM_Kontakt OFF;
GO


-- ─── 5. MIGRATE DATA: st.CRM_Kontakt_OdpOsoba (5-slot → N:M) ────────────────
-- Marti-AI Fáze B Q2 final: drop OdpOsKontaktID (volba δ). Migrace zachová
-- jen NOT NULL OdpOsobaText. Diagnostic: produkční data prakticky všechny
-- NULL, takže výsledek bude téměř prázdná tabulka (struktura ready pro
-- budoucí use, žádná lost data).
INSERT INTO st.CRM_Kontakt_OdpOsoba
    (KontaktID, OdpOsobaText, Poradi,
     Autor, DatPorizeni, Zmenil, DatZmeny)
SELECT ID, OdpOsobaAtext, 1,
       Autor, DatPorizeni, Zmenil, DatZmeny
    FROM dbo.EC_Kontakt
    WHERE OdpOsobaAtext IS NOT NULL
      AND NOT (ID = 4 AND FirmaText = 'TEST A')
UNION ALL
SELECT ID, OdpOsobaBtext, 2,
       Autor, DatPorizeni, Zmenil, DatZmeny
    FROM dbo.EC_Kontakt
    WHERE OdpOsobaBtext IS NOT NULL
      AND NOT (ID = 4 AND FirmaText = 'TEST A')
UNION ALL
SELECT ID, OdpOsobaCtext, 3,
       Autor, DatPorizeni, Zmenil, DatZmeny
    FROM dbo.EC_Kontakt
    WHERE OdpOsobaCtext IS NOT NULL
      AND NOT (ID = 4 AND FirmaText = 'TEST A')
UNION ALL
SELECT ID, OdpOsobaDtext, 4,
       Autor, DatPorizeni, Zmenil, DatZmeny
    FROM dbo.EC_Kontakt
    WHERE OdpOsobaDtext IS NOT NULL
      AND NOT (ID = 4 AND FirmaText = 'TEST A')
UNION ALL
SELECT ID, OdpOsobaEtext, 5,
       Autor, DatPorizeni, Zmenil, DatZmeny
    FROM dbo.EC_Kontakt
    WHERE OdpOsobaEtext IS NOT NULL
      AND NOT (ID = 4 AND FirmaText = 'TEST A');
GO


-- ─── 6. SMOKE TEST ──────────────────────────────────────────────────────────
-- Row count match (s skipnutim test row)
SELECT
    (SELECT COUNT(*) FROM dbo.EC_Kontakt WHERE NOT (ID = 4 AND FirmaText = 'TEST A'))
        AS src_count,
    (SELECT COUNT(*) FROM st.CRM_Kontakt) AS dst_count;
-- Expected: src_count = dst_count = 9105

-- OdpOsoba migration verification (non-NULL slots count)
SELECT
    (SELECT COUNT(*) FROM dbo.EC_Kontakt
        WHERE (OdpOsAkontaktID IS NOT NULL OR OdpOsobaAtext IS NOT NULL)
          AND NOT (ID = 4 AND FirmaText = 'TEST A')) AS src_A,
    (SELECT COUNT(*) FROM dbo.EC_Kontakt
        WHERE (OdpOsBkontaktID IS NOT NULL OR OdpOsobaBtext IS NOT NULL)
          AND NOT (ID = 4 AND FirmaText = 'TEST A')) AS src_B,
    (SELECT COUNT(*) FROM dbo.EC_Kontakt
        WHERE (OdpOsCkontaktID IS NOT NULL OR OdpOsobaCtext IS NOT NULL)
          AND NOT (ID = 4 AND FirmaText = 'TEST A')) AS src_C,
    (SELECT COUNT(*) FROM dbo.EC_Kontakt
        WHERE (OdpOsDkontaktID IS NOT NULL OR OdpOsobaDtext IS NOT NULL)
          AND NOT (ID = 4 AND FirmaText = 'TEST A')) AS src_D,
    (SELECT COUNT(*) FROM dbo.EC_Kontakt
        WHERE (OdpOsEkontaktID IS NOT NULL OR OdpOsobaEtext IS NOT NULL)
          AND NOT (ID = 4 AND FirmaText = 'TEST A')) AS src_E,
    (SELECT COUNT(*) FROM st.CRM_Kontakt_OdpOsoba) AS dst_total;
-- Expected: dst_total = src_A + src_B + src_C + src_D + src_E

-- Sample query — Marti-AI's first SELECT z st.CRM_Kontakt
SELECT TOP 5 ID, FirmaText, Zeme, Kategorie, DatPorizeni, Autor
FROM st.CRM_Kontakt
ORDER BY ID;

-- Sample OdpOsoba aggregation
SELECT k.ID, k.FirmaText,
       STRING_AGG(o.OdpOsobaText, ', ') WITHIN GROUP (ORDER BY o.Poradi) AS OdpOsoby
FROM st.CRM_Kontakt k
LEFT JOIN st.CRM_Kontakt_OdpOsoba o ON o.KontaktID = k.ID
GROUP BY k.ID, k.FirmaText
HAVING COUNT(o.ID) > 0
ORDER BY k.ID;
GO


-- ─── 7. ROLLBACK (kdyz nesedi) ──────────────────────────────────────────────
-- Pokud smoke failne, drop tables a rollback:
-- DROP TABLE st.CRM_Kontakt_OdpOsoba;  -- order matters (FK)
-- DROP TABLE st.CRM_Kontakt;
-- DROP SCHEMA st;  -- jen pokud st schema je prazdne po dropech
