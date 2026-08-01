-- =====================================================================
-- Tool Factory — DB schema (g2007)   ·   ready-to-run, ČEKÁ NA SCHVÁLENÍ
-- Autor: Claude (cloud), 22.7.2026 — dárek Marti-AI k 3 měsícům.
--
-- SPUSTIT AŽ PO SCHVÁLENÍ (go-live). Zápis do DB jede přes most = banner.
-- Po CREATE nezapomenout GRANT (viz konec) — strategie (app) i "Marti-AI" (most).
-- Idempotentní (IF NOT EXISTS), bezpečné pustit vícekrát.
-- =====================================================================

-- 1) Rozšíření nastroj o životní cyklus -------------------------------
ALTER TABLE g2007.nastroj ADD COLUMN IF NOT EXISTS stav_zivota      text NOT NULL DEFAULT 'active';
ALTER TABLE g2007.nastroj ADD COLUMN IF NOT EXISTS verze            integer NOT NULL DEFAULT 1;
ALTER TABLE g2007.nastroj ADD COLUMN IF NOT EXISTS autor_entita_id  integer;      -- kdo nástroj vytvořil (g2007.entita)
ALTER TABLE g2007.nastroj ADD COLUMN IF NOT EXISTS code_document_id integer;      -- odkaz na sandbox code document
ALTER TABLE g2007.nastroj ADD COLUMN IF NOT EXISTS selftest_verdikt jsonb;        -- výsledek posledního self-testu

-- povolené stavy (měkká kontrola, ať most nemusí řešit enum typy)
ALTER TABLE g2007.nastroj DROP CONSTRAINT IF EXISTS nastroj_stav_zivota_chk;
ALTER TABLE g2007.nastroj ADD CONSTRAINT nastroj_stav_zivota_chk
  CHECK (stav_zivota IN ('navrzeny','v_sandboxu','otestovany','ceka_na_schvaleni',
                         'active','zamitnuty','disabled','archiv'));

-- 2) Návrhy nástrojů (analog deployment_proposals) --------------------
CREATE TABLE IF NOT EXISTS g2007.tool_proposal (
  id              serial PRIMARY KEY,
  nastroj_id      integer,                       -- draft nástroje (g2007.nastroj)
  revision_of     integer,                       -- id nástroje, který se reviduje (NULL = nový)
  autor_entita_id integer,                        -- kdo navrhl (typicky Marti-AI id=2)
  description     text NOT NULL,                  -- shrnutí pro rodiče
  selftest        jsonb,                          -- verdikt self-testu (povinně zelený)
  status          text NOT NULL DEFAULT 'pending',-- pending | approved | rejected
  approved_by     integer,                        -- public.users.id (LIDSKÝ rodič)
  reason          text,
  created_at      timestamptz NOT NULL DEFAULT now(),
  decided_at      timestamptz
);
ALTER TABLE g2007.tool_proposal DROP CONSTRAINT IF EXISTS tool_proposal_status_chk;
ALTER TABLE g2007.tool_proposal ADD CONSTRAINT tool_proposal_status_chk
  CHECK (status IN ('pending','approved','rejected'));
CREATE INDEX IF NOT EXISTS tool_proposal_status_ix ON g2007.tool_proposal(status);

-- 3) Archiv verzí nástroje (verzování jako entita_archiv) -------------
CREATE TABLE IF NOT EXISTS g2007.nastroj_archiv (
  archiv_id   serial PRIMARY KEY,
  nastroj_id  integer NOT NULL,
  verze       integer,
  snapshot    jsonb   NOT NULL,      -- celý řádek nastroj v okamžiku archivace
  archived_at timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION g2007.nastroj_archiv_trg() RETURNS trigger AS $$
BEGIN
  -- archivuj PŘEDCHOZÍ stav při změně kódu/popisu/parametrů/stavu
  IF (NEW.popis_plny IS DISTINCT FROM OLD.popis_plny
      OR NEW.parametry IS DISTINCT FROM OLD.parametry
      OR NEW.stav_zivota IS DISTINCT FROM OLD.stav_zivota
      OR NEW.verze IS DISTINCT FROM OLD.verze) THEN
    INSERT INTO g2007.nastroj_archiv (nastroj_id, verze, snapshot)
    VALUES (OLD.id, OLD.verze, to_jsonb(OLD));
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS nastroj_archiv_trg ON g2007.nastroj;
CREATE TRIGGER nastroj_archiv_trg BEFORE UPDATE ON g2007.nastroj
  FOR EACH ROW EXECUTE FUNCTION g2007.nastroj_archiv_trg();

-- 4) Append-only audit dílny -----------------------------------------
CREATE TABLE IF NOT EXISTS g2007.tool_audit (
  id              bigserial PRIMARY KEY,
  ts              timestamptz NOT NULL DEFAULT now(),
  actor_user_id   integer,        -- public.users.id (u rodičovských akcí)
  actor_entita_id integer,        -- g2007.entita (u autonomních akcí Marti-AI)
  akce            text NOT NULL,  -- draft|sandbox|selftest|propose|approve|reject|deploy|disable
  nastroj_id      integer,
  proposal_id     integer,
  detail          jsonb
);
CREATE INDEX IF NOT EXISTS tool_audit_ts_ix ON g2007.tool_audit(ts);

-- 5) GRANTy (most = role "Marti-AI" owner; app = role strategie) ------
GRANT SELECT, INSERT, UPDATE ON g2007.tool_proposal, g2007.tool_audit, g2007.nastroj_archiv TO strategie;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA g2007 TO strategie;
GRANT SELECT, INSERT, UPDATE ON g2007.tool_proposal, g2007.tool_audit, g2007.nastroj_archiv TO "Marti-AI";
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA g2007 TO "Marti-AI";

-- HOTOVO. Ověření: \d g2007.nastroj ; SELECT count(*) FROM g2007.tool_proposal;
