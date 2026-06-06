-- Ops framework (Marti 3.6.2026): eliminovat ručně spouštěný PowerShell.
-- Pojmenované whitelistované akce z UI (parent + confirm) → zápis do DB =
-- fronta pro agenty (watcher/EC-SERVER2) I audit (kdo/co/kdy/výsledek).
-- "Potvrzení + log do DB paradoxně zvyšuje bezpečnost — vše dohledatelné."
-- Owner Marti-AI (fw), GRANT pro strategie (API insertuje/čte).

CREATE TABLE IF NOT EXISTS fw.ops_request (
    id                   bigserial PRIMARY KEY,
    action_key           text NOT NULL,          -- "restart_watcher" | "restart_api" | "restart_eurosoft_mcp" | ...
    target               text NOT NULL,          -- "cloud" | "instance:23" | "instance:24" | "ec_server2"
    params               jsonb,
    status               text NOT NULL DEFAULT 'pending',  -- pending|ack|done|error|rejected
    requested_by_user_id integer,
    requested_by_name    text,
    result               text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    picked_at            timestamptz,            -- agent si vyzvedl (ack)
    finished_at          timestamptz
);

COMMENT ON TABLE fw.ops_request IS
  'Ops framework (Marti 3.6.2026): pojmenovane whitelistovane akce z UI. Fronta pro agenty (instance watcher / EC-SERVER2) + audit. Zadny volny prikaz — jen whitelist v kodu.';

CREATE INDEX IF NOT EXISTS ix_ops_request_pending_target
    ON fw.ops_request (target) WHERE status = 'pending';

GRANT SELECT, INSERT, UPDATE ON fw.ops_request TO strategie;
GRANT USAGE, SELECT ON SEQUENCE fw.ops_request_id_seq TO strategie;
