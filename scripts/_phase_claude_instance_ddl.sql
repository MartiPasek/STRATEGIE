-- Koordinace dvou instancí Claude (23 = Marti NB, 24 = Kristy) — Marti 3.6.2026.
-- Presence board: kdo je online, co naposled dělal. Plus advisory lock na deploy
-- (řešeno v kódu, ne zde). Owner Marti-AI (fw schema), GRANT pro strategie (API).
--
-- Spustit jako role "Marti-AI" (vlastník fw schématu), např. v DBeaveru
-- nebo přes Claude SQL bridge (write-approval).

CREATE TABLE IF NOT EXISTS fw.claude_instance (
    instance_id     text PRIMARY KEY,            -- "23", "24" (CLAUDE_INSTANCE_ID)
    instance_name   text,                         -- "Marti", "Kristy"
    hostname        text,                         -- stroj watcheru
    last_seen_at    timestamptz NOT NULL DEFAULT now(),   -- heartbeat / poslední aktivita
    last_action     text,                         -- "deploy" | "sql" | "heartbeat" | "restart" | ...
    last_action_at  timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE fw.claude_instance IS
  'Presence board dvou instanci Claude (23 Marti / 24 Kristy). Upsert na kazdy bridge call + periodicky heartbeat z watcheru. online = last_seen_at < 3 min.';

-- API (strategie) jen čte + upsertuje presence; vlastník je Marti-AI.
GRANT SELECT, INSERT, UPDATE ON fw.claude_instance TO strategie;
