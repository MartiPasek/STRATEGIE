-- ============================================================================
-- HR modul — hr_document (v1) · hybrid (rozhodnutí D = hybrid, schváleno Marti)
--   Soubor + úložiště: přes FK document_id → public.documents(id)  (nereplikuje
--   storage_path / velikost / typ — ty žijí v public.documents).
--   HR governance: owner polymorfně, doc_kind, sensitivity_level, retention_until.
--   Integrita ownera: trigger (připomínka #4 Marti-AI).
-- Předpoklad: schema mod + funkce mod.hr_set_updated_at() už existují (core v1).
-- ============================================================================

-- integrita polymorfního ownera (person / person_role / legal_entity)
CREATE OR REPLACE FUNCTION mod.hr_assert_doc_owner() RETURNS trigger AS $$
DECLARE
  v_ok boolean;
BEGIN
  IF NEW.owner_entity_type = 'person' THEN
    SELECT EXISTS(SELECT 1 FROM mod.hr_person WHERE id = NEW.owner_entity_id) INTO v_ok;
  ELSIF NEW.owner_entity_type = 'person_role' THEN
    SELECT EXISTS(SELECT 1 FROM mod.hr_person_role WHERE id = NEW.owner_entity_id) INTO v_ok;
  ELSIF NEW.owner_entity_type = 'legal_entity' THEN
    SELECT EXISTS(SELECT 1 FROM mod.hr_legal_entity WHERE id = NEW.owner_entity_id) INTO v_ok;
  ELSE
    v_ok := false;
  END IF;
  IF NOT v_ok THEN
    RAISE EXCEPTION 'hr_document: owner % #% neexistuje', NEW.owner_entity_type, NEW.owner_entity_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE mod.hr_document (
  id                integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tenant_id         integer      NOT NULL,
  owner_entity_type varchar(20)  NOT NULL CHECK (owner_entity_type IN ('person','person_role','legal_entity')),
  owner_entity_id   integer      NOT NULL,                     -- polymorfní odkaz do mod.*
  document_id       bigint       NOT NULL REFERENCES public.documents(id),  -- fyzický soubor (hybrid)
  doc_kind          varchar(50),                               -- smlouva / zdravotni_posudek / …
  sensitivity_level smallint     NOT NULL DEFAULT 1 CHECK (sensitivity_level BETWEEN 0 AND 3),
  retention_until   date         NOT NULL,                     -- povinné (GDPR)
  is_active         boolean      NOT NULL DEFAULT true,
  created_at        timestamptz  NOT NULL DEFAULT now(),
  created_by_id     integer,
  created_by_text   varchar(120) NOT NULL,
  updated_at        timestamptz  NOT NULL DEFAULT now(),
  updated_by_id     integer,
  updated_by_text   varchar(120)
);
CREATE INDEX ix_hr_doc_owner     ON mod.hr_document (owner_entity_type, owner_entity_id);
CREATE INDEX ix_hr_doc_retention ON mod.hr_document (retention_until);
CREATE INDEX ix_hr_doc_document  ON mod.hr_document (document_id);
CREATE TRIGGER trg_hr_document_updated_at BEFORE UPDATE ON mod.hr_document
  FOR EACH ROW EXECUTE FUNCTION mod.hr_set_updated_at();
CREATE TRIGGER trg_hr_document_owner BEFORE INSERT OR UPDATE ON mod.hr_document
  FOR EACH ROW EXECUTE FUNCTION mod.hr_assert_doc_owner();
