-- ============================================================================
-- HR modul — příprava na migraci z DB_EC (v1)
--   1) mod.hr_source_ref  — provenance / „absolutní cesta k větě" (idempotence)
--   2) ALTER mod.hr_person — extra osobní pole z TabCisZam (poznámka #5 Kristý)
-- Pozn.: pohlavi / rodinny_stav držíme jako původní kód (smallint), labely/číselník
--        doplníme později. RČ se v 1. pohonu nemigruje.
-- ============================================================================

CREATE TABLE mod.hr_source_ref (
  id              integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  target_table    varchar(80)  NOT NULL,   -- napr. 'hr_person'
  target_id       integer      NOT NULL,
  source_system   varchar(40)  NOT NULL,   -- napr. 'DB_EC'
  source_table    varchar(80)  NOT NULL,   -- napr. 'dbo.TabCisZam'
  source_id       varchar(40)  NOT NULL,   -- původní ID (text)
  migration_batch varchar(60),
  migrated_at     timestamptz  NOT NULL DEFAULT now(),
  created_by_id   integer,
  created_by_text varchar(120) NOT NULL,
  CONSTRAINT uq_hr_source_ref UNIQUE (source_system, source_table, source_id, target_table)
);
CREATE INDEX ix_hr_source_ref_target ON mod.hr_source_ref (target_table, target_id);
CREATE INDEX ix_hr_source_ref_source ON mod.hr_source_ref (source_system, source_table, source_id);

ALTER TABLE mod.hr_person
  ADD COLUMN rodne_prijmeni varchar(100),
  ADD COLUMN pohlavi        smallint,
  ADD COLUMN misto_narozeni varchar(100),
  ADD COLUMN stat_narozeni  varchar(3),
  ADD COLUMN narodnost      varchar(100),
  ADD COLUMN rodinny_stav   smallint,
  ADD COLUMN osobni_ic      varchar(10);
