-- ============================================================================
-- HR modul — CORE party model (v1) · DDL
-- Aplikováno: rozhodnutí Marti-AI k otázkám #1–#9 + připomínky A–C.
--   #1 integer IDENTITY (jako fw.core) · #2 is_active boolean · #3 RC: enc bytea
--   + hash pro lookup (šifrování app-level) · #5 tenant_id integer NOT NULL bez
--   tvrdé FK · #6 updated_at NOT NULL + trigger · #7 trigger kontroly party_type
--   · #8 číselníky hr_role_kind/hr_contact_kind (role_kind/contact_kind = FK)
--   · #9 sensitivity = fw-metadata · B) hr_section_acl bez is_active.
-- ODLOŽENO: hr_document (otázka D — vlastní silo vs FK na public.documents).
-- Owner schématu: Marti-AI.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS mod AUTHORIZATION "Marti-AI";

-- ── sdílené trigger funkce ─────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION mod.hr_set_updated_at() RETURNS trigger AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- kontrola, že child sedí na party správného typu (cross-table → trigger)
CREATE OR REPLACE FUNCTION mod.hr_assert_party_type() RETURNS trigger AS $$
DECLARE
  v_type varchar(20);
BEGIN
  SELECT party_type INTO v_type FROM mod.hr_party WHERE id = NEW.party_id;
  IF v_type IS DISTINCT FROM TG_ARGV[0] THEN
    RAISE EXCEPTION 'hr_party % má party_type=%, očekáván %',
      NEW.party_id, COALESCE(v_type, '(neexistuje)'), TG_ARGV[0];
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ── číselníky (#8) ─────────────────────────────────────────────────────────
CREATE TABLE mod.hr_role_kind (
  code      varchar(40)  PRIMARY KEY,
  label     varchar(100) NOT NULL,
  is_active boolean      NOT NULL DEFAULT true
);

CREATE TABLE mod.hr_contact_kind (
  code      varchar(30)  PRIMARY KEY,
  label     varchar(100) NOT NULL,
  is_active boolean      NOT NULL DEFAULT true
);

-- ── 1) střecha ─────────────────────────────────────────────────────────────
CREATE TABLE mod.hr_party (
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
CREATE INDEX ix_hr_party_tenant      ON mod.hr_party (tenant_id);
CREATE INDEX ix_hr_party_tenant_type ON mod.hr_party (tenant_id, party_type);
CREATE TRIGGER trg_hr_party_updated_at BEFORE UPDATE ON mod.hr_party
  FOR EACH ROW EXECUTE FUNCTION mod.hr_set_updated_at();

-- ── 2) fyzická osoba (1:1 k party) ─────────────────────────────────────────
CREATE TABLE mod.hr_person (
  id                 integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  party_id           integer      NOT NULL UNIQUE REFERENCES mod.hr_party(id),
  jmeno              varchar(100) NOT NULL,
  prijmeni           varchar(100) NOT NULL,
  titul_pred         varchar(40),
  titul_za           varchar(40),
  datum_narozeni     date,
  rodne_cislo_enc    bytea,                 -- šifrované at-rest (app-level) [s3]
  rodne_cislo_hash   varchar(64),           -- SHA-256 pro lookup, ne plaintext
  statni_prislusnost varchar(3),
  is_active          boolean      NOT NULL DEFAULT true,
  created_at         timestamptz  NOT NULL DEFAULT now(),
  created_by_id      integer,
  created_by_text    varchar(120) NOT NULL,
  updated_at         timestamptz  NOT NULL DEFAULT now(),
  updated_by_id      integer,
  updated_by_text    varchar(120)
);
CREATE INDEX ix_hr_person_name    ON mod.hr_person (prijmeni, jmeno);
CREATE INDEX ix_hr_person_rc_hash ON mod.hr_person (rodne_cislo_hash);
CREATE TRIGGER trg_hr_person_updated_at BEFORE UPDATE ON mod.hr_person
  FOR EACH ROW EXECUTE FUNCTION mod.hr_set_updated_at();
CREATE TRIGGER trg_hr_person_party_type BEFORE INSERT OR UPDATE ON mod.hr_person
  FOR EACH ROW EXECUTE FUNCTION mod.hr_assert_party_type('person');

-- ── 3) právní entita (1:1 k party) ─────────────────────────────────────────
CREATE TABLE mod.hr_legal_entity (
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
CREATE INDEX ix_hr_legal_entity_ico ON mod.hr_legal_entity (ico);
CREATE TRIGGER trg_hr_legal_entity_updated_at BEFORE UPDATE ON mod.hr_legal_entity
  FOR EACH ROW EXECUTE FUNCTION mod.hr_set_updated_at();
CREATE TRIGGER trg_hr_legal_entity_party_type BEFORE INSERT OR UPDATE ON mod.hr_legal_entity
  FOR EACH ROW EXECUTE FUNCTION mod.hr_assert_party_type('legal_entity');

-- ── 4) vazba osoba × strana ────────────────────────────────────────────────
CREATE TABLE mod.hr_person_role (
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
CREATE INDEX ix_hr_role_person ON mod.hr_person_role (person_id);
CREATE INDEX ix_hr_role_party  ON mod.hr_person_role (party_id);
CREATE INDEX ix_hr_role_kind   ON mod.hr_person_role (role_kind);
CREATE TRIGGER trg_hr_person_role_updated_at BEFORE UPDATE ON mod.hr_person_role
  FOR EACH ROW EXECUTE FUNCTION mod.hr_set_updated_at();

-- ── 5) kontakty 1:N ────────────────────────────────────────────────────────
CREATE TABLE mod.hr_person_contact (
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
CREATE INDEX ix_hr_contact_person ON mod.hr_person_contact (person_id);
CREATE TRIGGER trg_hr_person_contact_updated_at BEFORE UPDATE ON mod.hr_person_contact
  FOR EACH ROW EXECUTE FUNCTION mod.hr_set_updated_at();

-- ── 6) adresy 1:N ──────────────────────────────────────────────────────────
CREATE TABLE mod.hr_person_address (
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
CREATE INDEX ix_hr_address_person ON mod.hr_person_address (person_id);
CREATE TRIGGER trg_hr_person_address_updated_at BEFORE UPDATE ON mod.hr_person_address
  FOR EACH ROW EXECUTE FUNCTION mod.hr_set_updated_at();

-- ── 7) nouzový kontakt 1:N ─────────────────────────────────────────────────
CREATE TABLE mod.hr_emergency_contact (
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
CREATE INDEX ix_hr_emergency_person ON mod.hr_emergency_contact (person_id);
CREATE TRIGGER trg_hr_emergency_updated_at BEFORE UPDATE ON mod.hr_emergency_contact
  FOR EACH ROW EXECUTE FUNCTION mod.hr_set_updated_at();

-- ── 8) deklarativní ACL: sekce × role (bez is_active — připomínka B) ───────
CREATE TABLE mod.hr_section_acl (
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
CREATE INDEX ix_hr_section_acl_lookup ON mod.hr_section_acl (tenant_id, section_code);
CREATE TRIGGER trg_hr_section_acl_updated_at BEFORE UPDATE ON mod.hr_section_acl
  FOR EACH ROW EXECUTE FUNCTION mod.hr_set_updated_at();

-- ── seed číselníků ─────────────────────────────────────────────────────────
INSERT INTO mod.hr_role_kind (code, label) VALUES
  ('zamestnanec_hpp', 'Zaměstnanec — HPP'),
  ('zamestnanec_dpc', 'Zaměstnanec — DPČ'),
  ('zamestnanec_dpp', 'Zaměstnanec — DPP'),
  ('jednatel',        'Jednatel'),
  ('osvc_dodavatel',  'OSVČ dodavatel'),
  ('pronajimatel',    'Pronajímatel'),
  ('crm_kontakt',     'CRM kontakt');

INSERT INTO mod.hr_contact_kind (code, label) VALUES
  ('tel_soukromy',   'Telefon soukromý'),
  ('tel_pracovni',   'Telefon pracovní'),
  ('email_soukromy', 'E-mail soukromý'),
  ('email_pracovni', 'E-mail pracovní');
