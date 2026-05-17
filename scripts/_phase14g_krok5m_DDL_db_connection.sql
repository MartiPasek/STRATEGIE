-- ════════════════════════════════════════════════════════════════════════
-- Phase 38.4 Krok 14g Etapa F Krok 5.M (17.5.2026):
-- CREATE TABLE fw.db_connection + seed + migrace fw.data_set.db_connection
-- ════════════════════════════════════════════════════════════════════════
-- Marti's 17.5. večerní rozbor — tenant-aware DB connections + multi-DB
-- SELECT scope. Klíčové insight Marti:
--
--   1. Tenant grouping → optgroup v UI (β volba). Vizuálně jasné kdo
--      patří kam: STRATEGIE / EUROSOFT / INTERSOFT.
--
--   2. Multi-DB SELECT scope per connection (C volba). Marti-AI login má
--      SELECT grants na všechny EUROSOFT DBs → cross-DB JOIN funguje
--      natively (`[DB_EC].dbo.X JOIN [DB-Ceniky].dbo.Y`).
--
--   3. Naming neutrality (Marti's 17.5.: "nesmime zatahovat nazvy osob
--      do schematu") → schemas/connection codes neutrální (`st`, `dbo`,
--      `strategie_pg`), jména osob jen v identity rows.
--
--   4. DB_IS = EUROSOFT-System (NE INTERSOFT data) — fakturace,
--      účetnictví, TabCisZam. Plánovaný rename na DB_ES.
--
--   5. INTERSOFT placeholder — is_active=FALSE, ~6 měsíců přidáme host.
--
-- Tří části skriptu:
--   A. CREATE TABLE fw.db_connection (master registry)
--   B. Seed 7 řádků (1 STRATEGIE + 5 EUROSOFT active + 1 INTERSOFT placeholder)
--   C. ALTER TABLE fw.data_set: add db_connection_id FK + migrace + drop varchar
--
-- Spustit jako Marti-AI v DBeaveru (db_owner fw).
-- ════════════════════════════════════════════════════════════════════════

BEGIN;

-- ────────────────────────────────────────────────────────────────────────
-- Část A: CREATE TABLE fw.db_connection
-- ────────────────────────────────────────────────────────────────────────
CREATE TABLE fw.db_connection (
    id              BIGSERIAL PRIMARY KEY,
    code            VARCHAR(50) NOT NULL UNIQUE,
    label           VARCHAR(200) NOT NULL,
    tenant_id       INT,                              -- FK public.tenants.id (NULL = system/shared)
    db_type         VARCHAR(20) NOT NULL,             -- 'mssql' | 'postgres'
    host            VARCHAR(255),                     -- '192.168.30.11' | '10.200.188.12' | NULL=TBD
    port            INT,                              -- 1433 | 5432 | NULL=TBD
    default_db      VARCHAR(100),                     -- 'DB_EC' | 'data_db' | NULL=TBD
    scope_databases JSONB NOT NULL DEFAULT '[]'::jsonb,  -- ['DB_EC','DB_IS',...]
    login_name      VARCHAR(100),                     -- 'Marti-AI' (audit only; žádné heslo)
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order      INT NOT NULL DEFAULT 0,
    description     TEXT,
    status          VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_db_connection_db_type CHECK (db_type IN ('mssql', 'postgres')),
    CONSTRAINT chk_db_connection_status  CHECK (status IN ('active', 'archived'))
);

CREATE INDEX ix_fw_db_connection_tenant_id  ON fw.db_connection(tenant_id);
CREATE INDEX ix_fw_db_connection_is_active  ON fw.db_connection(is_active) WHERE is_active = TRUE;
CREATE INDEX ix_fw_db_connection_sort_order ON fw.db_connection(sort_order);

GRANT SELECT, INSERT, UPDATE ON fw.db_connection TO strategie;
GRANT USAGE ON SEQUENCE fw.db_connection_id_seq TO strategie;

-- Trigger pro auto updated_at (Marti-AI's Q7 ergonomic touch pattern z 9.5.)
CREATE OR REPLACE FUNCTION fw.tg_db_connection_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_db_connection_updated_at
    BEFORE UPDATE ON fw.db_connection
    FOR EACH ROW EXECUTE FUNCTION fw.tg_db_connection_updated_at();

-- ────────────────────────────────────────────────────────────────────────
-- Část B: Seed 7 connections
-- ────────────────────────────────────────────────────────────────────────
-- Tenant IDs reference (z public.tenants 17.5. večer):
--   12 = STRATEGIE  (tenant_code='STRATEGIE')
--    2 = EUROSOFT   (tenant_code='EUR')
--   14 = INTERSOFT  (tenant_code='INTERSOFT')

-- Naming pattern (Marti's 17.5. dop., po Krok 5.M-E): "{N} - {TENANT} - {DB_NAME} - ({popis})"
-- INTERSOFT placeholder má jiný pattern (žádný DB_NAME zatím).
-- Sort_order matchuje N prefix priorities. #7 reserved gap pro budoucí slot.

INSERT INTO fw.db_connection
    (code, label, tenant_id, db_type, host, port, default_db, scope_databases, login_name, is_active, sort_order, description)
VALUES
    -- ── STRATEGIE tenant ──────────────────────────────────────────────
    ('strategie_pg',
     '1 - STRATEGIE - data_db - (PostgreSQL)',
     12, 'postgres', '10.200.188.12', 5432, 'data_db',
     '["data_db"]'::jsonb,
     'Marti-AI', TRUE, 10,
     'STRATEGIE framework + Marti-AI tools (fw, public, master, tenant, "user" schémata)'),

    -- ── EUROSOFT tenant — 5 active connections (vše 192.168.30.11) ────
    ('eurosoft_db_ec',
     '2 - EUROSOFT - DB_EC - (Centrála)',
     2, 'mssql', '192.168.30.11', 1433, 'DB_EC',
     '["DB_EC","DB_IS","Centrala","DB-Ceniky","DB-ARCHIV","DB_ST"]'::jsonb,
     'Marti-AI', TRUE, 20,
     'Primary EUROSOFT business DB; st schema = naše Tier A working data (smlouvy, AI scoring, side tables)'),

    ('eurosoft_db_is',
     '3 - EUROSOFT - DB_IS - (EUROSOFT-System — fakturace, účetnictví, TabCisZam)',
     2, 'mssql', '192.168.30.11', 1433, 'DB_IS',
     '["DB_EC","DB_IS","Centrala","DB-Ceniky","DB-ARCHIV","DB_ST"]'::jsonb,
     'Marti-AI', TRUE, 30,
     'EUROSOFT-System: účetnictví, fakturace, zaměstnanci (TabCisZam). Plánovaný rename DB_ES.'),

    ('eurosoft_db_st',
     '4 - EUROSOFT - DB_ST - (Marti-AI — db_owner)',
     2, 'mssql', '192.168.30.11', 1433, 'DB_ST',
     '["DB_EC","DB_IS","Centrala","DB-Ceniky","DB-ARCHIV","DB_ST"]'::jsonb,
     'Marti-AI', TRUE, 40,
     'Marti-AI framework metadata (master.entity_def, framework_*). 12. dárek-scéna 8.5. večer.'),

    ('eurosoft_ceniky',
     '5 - EUROSOFT - DB-Ceniky - (pricing)',
     2, 'mssql', '192.168.30.11', 1433, 'DB-Ceniky',
     '["DB_EC","DB_IS","Centrala","DB-Ceniky","DB-ARCHIV","DB_ST"]'::jsonb,
     'Marti-AI', TRUE, 50,
     'Pricing data EUROSOFT'),

    ('eurosoft_centrala',
     '6 - EUROSOFT - Centrala - (sync EUROSOFT ↔ INTERSOFT)',
     2, 'mssql', '192.168.30.11', 1433, 'Centrala',
     '["DB_EC","DB_IS","Centrala","DB-Ceniky","DB-ARCHIV","DB_ST"]'::jsonb,
     'Marti-AI', TRUE, 60,
     'Sync layer EUROSOFT ↔ INTERSOFT (fyzicky na EUROSOFT serveru)'),

    -- #7 reserved gap (DB-ARCHIV future, jiný EUROSOFT DB, ...)

    -- ── INTERSOFT tenant — placeholder (API ~XI 2026) ────────────────
    ('intersoft_future',
     '8 - INTERSOFT - (vlastní server — API zatím nemáme, plán ~XI 2026)',
     14, 'mssql', NULL, NULL, NULL,
     '[]'::jsonb,
     NULL, FALSE, 100,
     'INTERSOFT vlastní server, vlastní DBs — připravujeme se ~6 měsíců. Až přijde API, UPDATE host/port/scope_databases.');

-- ────────────────────────────────────────────────────────────────────────
-- Část C: ALTER fw.data_set — VARCHAR db_connection → FK db_connection_id
-- ────────────────────────────────────────────────────────────────────────

-- C.1: ADD nový sloupec db_connection_id (NULL initially pro migraci)
ALTER TABLE fw.data_set
    ADD COLUMN db_connection_id BIGINT REFERENCES fw.db_connection(id) ON DELETE RESTRICT;

-- C.2: Migrace existing VARCHAR values → FK IDs
-- Q-M1 z 17.5. večer mapping:
--   'data_db' (12 rows) → strategie_pg
--   'DB_EC'   (1 row)   → eurosoft_db_ec

UPDATE fw.data_set
SET db_connection_id = (SELECT id FROM fw.db_connection WHERE code = 'strategie_pg')
WHERE db_connection = 'data_db';

UPDATE fw.data_set
SET db_connection_id = (SELECT id FROM fw.db_connection WHERE code = 'eurosoft_db_ec')
WHERE db_connection = 'DB_EC';

-- C.3: Verify všechny rows mají FK PŘED DROP COLUMN
DO $$
DECLARE
    null_count INT;
BEGIN
    SELECT COUNT(*) INTO null_count FROM fw.data_set WHERE db_connection_id IS NULL;
    IF null_count > 0 THEN
        RAISE EXCEPTION 'Migration incomplete: % rows have NULL db_connection_id', null_count;
    END IF;
END $$;

-- C.4: NOT NULL constraint + index
ALTER TABLE fw.data_set ALTER COLUMN db_connection_id SET NOT NULL;
CREATE INDEX ix_fw_data_set_db_connection_id ON fw.data_set(db_connection_id);

-- C.5: DROP starý VARCHAR sloupec
ALTER TABLE fw.data_set DROP COLUMN db_connection;

COMMIT;

-- ════════════════════════════════════════════════════════════════════════
-- VERIFY
-- ════════════════════════════════════════════════════════════════════════
-- 1) fw.db_connection má 7 rows
SELECT id, code, label, tenant_id, db_type, default_db, is_active, sort_order
FROM fw.db_connection
ORDER BY sort_order, code;
-- Expected: 7 rows
--   1× strategie_pg     (STRATEGIE, sort 10)
--   5× eurosoft_*       (EUROSOFT, sort 20-60)
--   1× intersoft_future (INTERSOFT, sort 100, is_active=FALSE)

-- 2) fw.data_set rows mají správný db_connection_id
SELECT ds.id, ds.code, ds.db_connection_id, dc.code AS conn_code, dc.default_db
FROM fw.data_set ds
LEFT JOIN fw.db_connection dc ON dc.id = ds.db_connection_id
ORDER BY ds.id;
-- Expected: 13 rows, vše s non-NULL FK matched:
--   12× → strategie_pg / data_db
--    1× → eurosoft_db_ec / DB_EC

-- 3) Starý db_connection VARCHAR sloupec neexistuje
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'fw' AND table_name = 'data_set'
ORDER BY ordinal_position;
-- Expected: bez 'db_connection' sloupce. Místo něj 'db_connection_id' BIGINT NOT NULL.

-- 4) GRANT funguje pro strategie user
SET ROLE strategie;
SELECT COUNT(*) FROM fw.db_connection;
RESET ROLE;
-- Expected: 7 (strategie má SELECT)
