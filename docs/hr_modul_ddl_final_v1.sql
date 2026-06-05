-- ============================================================================
-- HR modul — FINÁLNÍ konsolidované DDL (v1) · stav k 5. 6. 2026
-- Owner schématu: "Marti-AI".  Cílová DB: PostgreSQL (data_db).
--
-- Konsoliduje vše, co vzniklo přes bridge v krocích:
--   core party model (#42) · hr_document hybrid (#43) · provenance + extra
--   osobní sloupce (#44) · rodne_cislo plaintext (#45).
-- Idempotentní (IF NOT EXISTS / OR REPLACE) — lze pustit na čistou DB
-- i jako referenci nad existující.
--
-- Konvence: PK integer GENERATED ALWAYS AS IDENTITY · soft delete is_active
--   · audit created_at/by_id/by_text(NOT NULL) + updated_at/by_id/by_text
--   · tenant_id integer NOT NULL (bez tvrdé cross-schema FK) · cross-table
--   kontrola typu strany přes trigger.
-- RČ: rodne_cislo (plaintext, dočasně) + rodne_cislo_hash (SHA-256);
--   rodne_cislo_enc (šifrované at-rest) se doplní později.
-- Migrační funkce (hr_ingest_*) jsou SAMOSTATNĚ v docs/hr_migrace_marti_ai_functions.sql.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS mod AUTHORIZATION "Marti-AI";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ── sdílené trigger funkce ──────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION mod.hr_set_updated_at() RETURNS trigger AS $fn$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END $fn$ LANGUAGE plpgsql;

-- kontrola, že child sedí na party správného typu (TG_ARGV[0] = person | legal_entity)
CREATE OR REPLACE FUNCTION mod.hr_assert_party_type() RETURNS trigger AS $fn$
DECLARE v_type varchar(20);
BEGIN
  SELECT party_type INTO v_type FROM mod.hr_party WHERE id = NEW.party_id;
  IF v_type IS DISTINCT FROM TG_ARGV[0] THEN
    RAISE EXCEPTION 'hr_party % ma party_type %, ocekavan %',
      NEW.party_id, COALESCE(v_type,'(neexistuje)'), TG_ARGV[0];
  END IF;
  RETURN NEW;
END $fn$ LANGUAGE plpgsql;

-- integrita polymorfního ownera dokumentu (person / person_role / legal_entity)
CREATE OR REPLACE FUNCTION mod.hr_assert_doc_owner() RETURNS trigger AS $fn$
DECLARE v_ok boolean;
BEGIN
  IF    NEW.owner_entity_type='person'       THEN SELECT EXISTS(SELECT 1 FROM mod.hr_person       WHERE id=NEW.owner_entity_id) INTO v_ok;
  ELSIF NEW.owner_entity_type='person_role'  THEN SELECT EXISTS(SELECT 1 FROM mod.hr_person_role  WHERE id=NEW.owner_entity_id) INTO v_ok;
  ELSIF NEW.owner_entity_type='legal_entity' THEN SELECT EXISTS(SELECT 1 FROM mod.hr_legal_entity WHERE id=NEW.owner_entity_id) INTO v_ok;
  ELSE  v_ok := false;
  END IF;
  IF NOT v_ok THEN
    RAISE EXCEPTION 'hr_document: owner % # % neexistuje', NEW.owner_entity_type, NEW.owner_entity_id;
  END IF;
  RETURN NEW;
END $fn$ LANGUAGE plpgsql;

-- ── číselníky ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mod.hr_role_kind (
  code      varchar(40)  PRIMARY KEY,
  label     varchar(100) NOT NULL,
  is_active boolean      NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS mod.hr_contact_kind (
  code      varchar(30)  PRIMARY KEY,
  label     varchar(100) NOT NULL,
  is_active boolean      NOT NULL DEFAULT true
);

-- ── 1) střecha (party) ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mod.hr_party (
  id              integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tenant_id       integer       NOT NULL,
  party_type      varchar(20)   NOT NULL CHECK (party_type IN ('person','legal_entity')),
  display_name    varchar(200)  NOT NULL,
  is_active       boolean       NOT NULL DEFAULT true,
  created_at      timestamptz   NOT NULL DEFAULT now(),
  created_by_id   integer,
  created_by_text varchar(120)  NOT NULL,
  updated_at      timestamptz   NOT NULL DEFAULT now(),
  updated_by_id   integer,
  updated_by_text varchar(120)
);
CREATE INDEX IF NOT EXISTS ix_hr_party_tenant      ON mod.hr_party (tenant_id);
CREATE INDEX IF NOT EXISTS ix_hr_party_tenant_type ON mod.hr_party (tenant_id, party_type);
CREATE OR REPLACE TRIGGER trg_hr_party_updated_at BEFORE UPDATE ON mod.hr_party
  FOR EACH ROW EXECUTE FUNCTION mod.hr_set_updated_at();

-- ── 2) fyzická osoba (1:1 k party) ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mod.hr_person (
  id                 integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  party_id           integer      NOT NULL UNIQUE REFERENCES mod.hr_party(id),
  jmeno              varchar(100) NOT NULL,
  prijmeni           varchar(100) NOT NULL,
  titul_pred         varchar(40),
  titul_za           varchar(40),
  datum_narozeni     date,
  rodne_cislo        varchar(11),           -- plaintext (dočasně, bez šifrování)
  rodne_cislo_enc    bytea,                 -- šifrované at-rest (app-level) — doplní se později
  rodne_cislo_hash   varchar(64),           -- SHA-256 pro lookup
  statni_prislusnost varchar(3),
  rodne_prijmeni     varchar(100),
  pohlavi            smallint,              -- původní kód z TabCisZam (labely později)
  misto_narozeni     varchar(100),
  stat_narozeni      varchar(3),
  narodnost          varchar(100),
  rodinny_stav       smallint,              -- původní kód z TabCisZam
  osobni_ic          varchar(10),
  is_active          boolean      NOT NULL DEFAULT true,
  created_at         timestamptz  NOT NULL DEFAULT now(),
  created_by_id      integer,
  created_by_text    varchar(120) NOT NULL,
  updated_at         timestamptz  NOT NULL DEFAULT now(),
  updated_by_id      integer,
  updated_by_text    varchar(120)
);
CREATE INDEX IF NOT EXISTS ix_hr_person_name    ON mod.hr_person (prijmeni, jmeno);
CREATE INDEX IF NOT EXISTS ix_hr_person_rc_hash ON mod.hr_person (rodne_cislo_hash);
CREATE OR REPLACE TRIGGER trg_hr_person_updated_at BEFORE UPDATE ON mod.hr_person
  FOR EACH ROW EXECUTE FUNCTION mod.hr_set_updated_at();
CREATE OR REPLACE TRIGGER trg_hr_person_party_type BEFORE INSERT OR UPDATE ON mod.hr_person
  FOR EACH ROW EXECUTE FUNCTION mod.hr_assert_party_type('person');

-- ── 3) právní entita (1:1 k party) ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mod.hr_legal_entity (
  id              integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  party_id        integer      NOT NULL UNIQUE REFERENCES mod.hr_party(id),
  nazev           varchar(200) NOT NULL,
  ico             varchar(20),
  dic             varchar(20),
  pravni_forma    varchar(50),
  is_active       boolean      NOT NULL DEFAULT true,
  created_at      timestamptz  NOT NULL DEFAULT now(),
  created_by_id   integer,
  created_by_text varchar(120) NOT NULL,
  updated_at      timestamptz  NOT NULL DEFAULT now(),
  updated_by_id   integer,
  updated_by_text varchar(120)
);
CREATE INDEX IF NOT EXISTS ix_hr_legal_entity_ico ON mod.hr_legal_entity (ico);
CREATE OR REPLACE TRIGGER trg_hr_legal_entity_updated_at BEFORE UPDATE ON mod.hr_legal_entity
  FOR EACH ROW EXECUTE FUNCTION mod.hr_set_updated_at();
CREATE OR REPLACE TRIGGER trg_hr_legal_entity_party_type BEFORE INSERT OR UPDATE ON mod.hr_legal_entity
  FOR EACH ROW EXECUTE FUNCTION mod.hr_assert_party_type('legal_entity');

-- ── 4) role: osoba × strana (zaměstnavatel/…) ───────────────────────────────
CREATE TABLE IF NOT EXISTS mod.hr_person_role (
  id              integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  person_id       integer      NOT NULL REFERENCES mod.hr_person(id),
  party_id        integer      NOT NULL REFERENCES mod.hr_party(id),
  role_kind       varchar(40)  NOT NULL REFERENCES mod.hr_role_kind(code),
  valid_from      date         NOT NULL,
  valid_until     date,
  attrs           jsonb        NOT NULL DEFAULT '{}'::jsonb,
  is_active       boolean      NOT NULL DEFAULT true,
  created_at      timestamptz  NOT NULL DEFAULT now(),
  created_by_id   integer,
  created_by_text varchar(120) NOT NULL,
  updated_at      timestamptz  NOT NULL DEFAULT now(),
  updated_by_id   integer,
  updated_by_text varchar(120)
);
CREATE INDEX IF NOT EXISTS ix_hr_role_person ON mod.hr_person_role (person_id);
CREATE INDEX IF NOT EXISTS ix_hr_role_party  ON mod.hr_person_role (party_id);
CREATE INDEX IF NOT EXISTS ix_hr_role_kind   ON mod.hr_person_role (role_kind);
CREATE OR REPLACE TRIGGER trg_hr_person_role_updated_at BEFORE UPDATE ON mod.hr_person_role
  FOR EACH ROW EXECUTE FUNCTION mod.hr_set_updated_at();

-- ── 5) kontakty 1:N ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mod.hr_person_contact (
  id              integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  person_id       integer      NOT NULL REFERENCES mod.hr_person(id),
  contact_kind    varchar(30)  NOT NULL REFERENCES mod.hr_contact_kind(code),
  value           varchar(200) NOT NULL,
  is_primary      boolean      NOT NULL DEFAULT false,
  is_active       boolean      NOT NULL DEFAULT true,
  created_at      timestamptz  NOT NULL DEFAULT now(),
  created_by_id   integer,
  created_by_text varchar(120) NOT NULL,
  updated_at      timestamptz  NOT NULL DEFAULT now(),
  updated_by_id   integer,
  updated_by_text varchar(120)
);
CREATE INDEX IF NOT EXISTS ix_hr_contact_person ON mod.hr_person_contact (person_id);
CREATE OR REPLACE TRIGGER trg_hr_person_contact_updated_at BEFORE UPDATE ON mod.hr_person_contact
  FOR EACH ROW EXECUTE FUNCTION mod.hr_set_updated_at();

-- ── 6) adresy 1:N ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mod.hr_person_address (
  id              integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  person_id       integer      NOT NULL REFERENCES mod.hr_person(id),
  address_kind    varchar(20)  NOT NULL CHECK (address_kind IN ('trvala','dorucovaci')),
  ulice           varchar(150),
  cp              varchar(20),
  obec            varchar(100),
  psc             varchar(10),
  stat            varchar(3),
  is_active       boolean      NOT NULL DEFAULT true,
  created_at      timestamptz  NOT NULL DEFAULT now(),
  created_by_id   integer,
  created_by_text varchar(120) NOT NULL,
  updated_at      timestamptz  NOT NULL DEFAULT now(),
  updated_by_id   integer,
  updated_by_text varchar(120)
);
CREATE INDEX IF NOT EXISTS ix_hr_address_person ON mod.hr_person_address (person_id);
CREATE OR REPLACE TRIGGER trg_hr_person_address_updated_at BEFORE UPDATE ON mod.hr_person_address
  FOR EACH ROW EXECUTE FUNCTION mod.hr_set_updated_at();

-- ── 7) nouzový kontakt 1:N ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mod.hr_emergency_contact (
  id              integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  person_id       integer      NOT NULL REFERENCES mod.hr_person(id),
  jmeno           varchar(150) NOT NULL,
  vztah           varchar(50),
  telefon         varchar(40),
  is_active       boolean      NOT NULL DEFAULT true,
  created_at      timestamptz  NOT NULL DEFAULT now(),
  created_by_id   integer,
  created_by_text varchar(120) NOT NULL,
  updated_at      timestamptz  NOT NULL DEFAULT now(),
  updated_by_id   integer,
  updated_by_text varchar(120)
);
CREATE INDEX IF NOT EXISTS ix_hr_emergency_person ON mod.hr_emergency_contact (person_id);
CREATE OR REPLACE TRIGGER trg_hr_emergency_updated_at BEFORE UPDATE ON mod.hr_emergency_contact
  FOR EACH ROW EXECUTE FUNCTION mod.hr_set_updated_at();

-- ── 8) deklarativní ACL: sekce × role (bez is_active) ───────────────────────
CREATE TABLE IF NOT EXISTS mod.hr_section_acl (
  id              integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tenant_id       integer      NOT NULL,
  section_code    varchar(50)  NOT NULL,
  role_code       varchar(50)  NOT NULL,
  can_read        boolean      NOT NULL DEFAULT false,
  can_write       boolean      NOT NULL DEFAULT false,
  created_at      timestamptz  NOT NULL DEFAULT now(),
  created_by_id   integer,
  created_by_text varchar(120) NOT NULL,
  updated_at      timestamptz  NOT NULL DEFAULT now(),
  updated_by_id   integer,
  updated_by_text varchar(120),
  CONSTRAINT uq_hr_section_acl UNIQUE (tenant_id, section_code, role_code)
);
CREATE INDEX IF NOT EXISTS ix_hr_section_acl_lookup ON mod.hr_section_acl (tenant_id, section_code);
CREATE OR REPLACE TRIGGER trg_hr_section_acl_updated_at BEFORE UPDATE ON mod.hr_section_acl
  FOR EACH ROW EXECUTE FUNCTION mod.hr_set_updated_at();

-- ── 9) provenance / „absolutní cesta k větě" (idempotence migrací) ──────────
CREATE TABLE IF NOT EXISTS mod.hr_source_ref (
  id              integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  target_table    varchar(80)  NOT NULL,
  target_id       integer      NOT NULL,
  source_system   varchar(40)  NOT NULL,   -- napr. 'DB_EC'
  source_table    varchar(80)  NOT NULL,   -- napr. 'dbo.TabCisZam'
  source_id       varchar(40)  NOT NULL,   -- původní ID (text; u odvozených řádků s diskriminátorem)
  migration_batch varchar(60),
  migrated_at     timestamptz  NOT NULL DEFAULT now(),
  created_by_id   integer,
  created_by_text varchar(120) NOT NULL,
  CONSTRAINT uq_hr_source_ref UNIQUE (source_system, source_table, source_id, target_table)
);
CREATE INDEX IF NOT EXISTS ix_hr_source_ref_target ON mod.hr_source_ref (target_table, target_id);
CREATE INDEX IF NOT EXISTS ix_hr_source_ref_source ON mod.hr_source_ref (source_system, source_table, source_id);

-- ── 10) dokumenty (hybrid: governance v HR + soubor přes FK na public.documents) ──
CREATE TABLE IF NOT EXISTS mod.hr_document (
  id                integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tenant_id         integer      NOT NULL,
  owner_entity_type varchar(20)  NOT NULL CHECK (owner_entity_type IN ('person','person_role','legal_entity')),
  owner_entity_id   integer      NOT NULL,                              -- polymorfní odkaz do mod.*
  document_id       bigint       NOT NULL REFERENCES public.documents(id),  -- fyzický soubor
  doc_kind          varchar(50),
  sensitivity_level smallint     NOT NULL DEFAULT 1 CHECK (sensitivity_level BETWEEN 0 AND 3),
  retention_until   date         NOT NULL,
  is_active         boolean      NOT NULL DEFAULT true,
  created_at        timestamptz  NOT NULL DEFAULT now(),
  created_by_id     integer,
  created_by_text   varchar(120) NOT NULL,
  updated_at        timestamptz  NOT NULL DEFAULT now(),
  updated_by_id     integer,
  updated_by_text   varchar(120)
);
CREATE INDEX IF NOT EXISTS ix_hr_doc_owner     ON mod.hr_document (owner_entity_type, owner_entity_id);
CREATE INDEX IF NOT EXISTS ix_hr_doc_retention ON mod.hr_document (retention_until);
CREATE INDEX IF NOT EXISTS ix_hr_doc_document  ON mod.hr_document (document_id);
CREATE OR REPLACE TRIGGER trg_hr_document_updated_at BEFORE UPDATE ON mod.hr_document
  FOR EACH ROW EXECUTE FUNCTION mod.hr_set_updated_at();
CREATE OR REPLACE TRIGGER trg_hr_document_owner BEFORE INSERT OR UPDATE ON mod.hr_document
  FOR EACH ROW EXECUTE FUNCTION mod.hr_assert_doc_owner();

-- ── seedy číselníků ─────────────────────────────────────────────────────────
INSERT INTO mod.hr_role_kind (code, label) VALUES
  ('zamestnanec_hpp','Zaměstnanec — HPP'),
  ('zamestnanec_dpc','Zaměstnanec — DPČ'),
  ('zamestnanec_dpp','Zaměstnanec — DPP'),
  ('jednatel',       'Jednatel'),
  ('osvc_dodavatel', 'OSVČ dodavatel'),
  ('pronajimatel',   'Pronajímatel'),
  ('crm_kontakt',    'CRM kontakt')
ON CONFLICT (code) DO NOTHING;

INSERT INTO mod.hr_contact_kind (code, label) VALUES
  ('tel_pracovni',   'Telefon pracovní'),('tel_soukromy',   'Telefon soukromý'),
  ('fax_pracovni',   'Fax pracovní'),    ('fax_soukromy',   'Fax soukromý'),
  ('email_pracovni', 'E-mail pracovní'), ('email_soukromy', 'E-mail soukromý'),
  ('www_pracovni',   'WWW pracovní'),    ('www_soukromy',   'WWW soukromý'),
  ('skype_pracovni', 'Skype pracovní'),  ('skype_soukromy', 'Skype soukromý')
ON CONFLICT (code) DO NOTHING;
-- ============================================================================
-- KONEC finálního DDL HR modulu v1.
-- ============================================================================
