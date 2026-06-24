-- Univerzální bankovní napojení v1 — schéma (po konzultaci + schema-review Marti-AI 24.6.2026)
-- Tenant: EUROSOFT=2, STRATEGIE=12. Company: tenant.company (EC/ES/SS).
-- Princip: provider-agnostické, multi-tenant + multi-company, kredenciály v trezoru.
-- Zapracováno 6 bodů review Marti-AI + uzavření kruhu platba↔transakce.

-- 1) Provider (číselník bank/API)
CREATE TABLE IF NOT EXISTS tenant.bank_provider (
  id          bigserial PRIMARY KEY,
  kod         text NOT NULL UNIQUE,                 -- RB_PREMIUM_API
  nazev       text NOT NULL,
  base_url    text,
  auth_typ    text NOT NULL DEFAULT 'cert_mtls',
  schopnosti  jsonb NOT NULL DEFAULT '{}'::jsonb,   -- {statements,transactions,balances,payments}
  aktivni     boolean NOT NULL DEFAULT true,
  created_at  timestamptz NOT NULL DEFAULT now()
);

-- trigger fn pro updated_at (vlastní, bez kolize s existujícími)
CREATE OR REPLACE FUNCTION tenant.bank_set_updated_at() RETURNS trigger AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END; $$ LANGUAGE plpgsql;

-- 2) Connection (per firma per banka)  [review #1: updated/disabled audit]
CREATE TABLE IF NOT EXISTS tenant.bank_connection (
  id          bigserial PRIMARY KEY,
  tenant_id   integer NOT NULL,
  company_id  bigint,                               -- tenant.company (EC/ES/SS); NULL = celý tenant
  provider_id bigint NOT NULL REFERENCES tenant.bank_provider(id),
  nazev       text NOT NULL,
  stav        text NOT NULL DEFAULT 'active',       -- active/disabled
  vault_ref   text,                                 -- odkaz do trezoru (cert+heslo); NIKDY plaintext
  created_by  text,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now(),
  disabled_at timestamptz,
  disabled_by text
);
DROP TRIGGER IF EXISTS trg_bank_connection_upd ON tenant.bank_connection;
CREATE TRIGGER trg_bank_connection_upd BEFORE UPDATE ON tenant.bank_connection
  FOR EACH ROW EXECUTE FUNCTION tenant.bank_set_updated_at();

-- 3) Účty pod connection + scope flagy  [review #5: nazev/alias]
CREATE TABLE IF NOT EXISTS tenant.bank_connection_account (
  id            bigserial PRIMARY KEY,
  connection_id bigint NOT NULL REFERENCES tenant.bank_connection(id),
  cislo_uctu    text NOT NULL,
  nazev         text,                               -- "EC běžný CZK", "ES provozní"...
  mena          text NOT NULL DEFAULT 'CZK',
  sc_historie   boolean NOT NULL DEFAULT true,       -- Transakční historie
  sc_zustatky   boolean NOT NULL DEFAULT true,       -- Účty a zůstatky
  sc_vypisy     boolean NOT NULL DEFAULT true,       -- Výpisy
  sc_platby     boolean NOT NULL DEFAULT false,      -- Hromadné platby (write) — default OFF
  aktivni       boolean NOT NULL DEFAULT true
);

-- 4) Platební příkazy (Marti-AI navrhuje, ČLOVĚK schvaluje)  [review #2: zamítnutí trail]
CREATE TABLE IF NOT EXISTS tenant.bank_payment_order (
  id          bigserial PRIMARY KEY,
  account_id  bigint NOT NULL REFERENCES tenant.bank_connection_account(id),
  protiucet   text NOT NULL,
  castka      numeric(18,2) NOT NULL,
  mena        text NOT NULL DEFAULT 'CZK',
  vs text, zprava text,
  stav        text NOT NULL DEFAULT 'navrzeno',      -- navrzeno/schvaleno/odeslano/zamitnuto
  navrhl      text, navrhl_at timestamptz DEFAULT now(),
  schvalil    text, schvalil_at timestamptz,
  zamitl      text, zamitl_at timestamptz, zamitl_duvod text,
  odeslano_at timestamptz,
  poznamka    text
);

-- 5) STAGING (ne rovnou do deníku)  [review #3: partial unique; #kruh: payment_order_id]
CREATE TABLE IF NOT EXISTS tenant.bank_transaction_raw (
  id               bigserial PRIMARY KEY,
  account_id       bigint NOT NULL REFERENCES tenant.bank_connection_account(id),
  ext_id           text,                             -- id transakce u banky (dedup)
  datum            date,
  castka           numeric(18,2),
  mena             text,
  smer             text,                             -- in/out
  protiucet        text,
  vs text, ks text, ss text,
  zprava           text,
  raw              jsonb,                            -- původní payload
  stav_parovani    text NOT NULL DEFAULT 'nove',     -- nove/sparovano/ignorovano
  denik_id         bigint,                           -- po zaúčtování → tenant.ucetni_denik
  payment_order_id bigint REFERENCES tenant.bank_payment_order(id),  -- odchozí platba ↔ transakce
  imported_at      timestamptz NOT NULL DEFAULT now()
);
-- partial unique: NULL ext_id se nepáruje (Postgres NULL != NULL by jinak pustil duplicity)
CREATE UNIQUE INDEX IF NOT EXISTS uq_bank_tx_raw_extid
  ON tenant.bank_transaction_raw (account_id, ext_id) WHERE ext_id IS NOT NULL;

-- 6) Audit append-only  [review #4: payment_order_id]
CREATE TABLE IF NOT EXISTS tenant.bank_api_log (
  id               bigserial PRIMARY KEY,
  connection_id    bigint,
  account_id       bigint,
  payment_order_id bigint REFERENCES tenant.bank_payment_order(id),  -- jen u platebních operací
  operace          text NOT NULL,                    -- get_transactions/get_balance/get_statement/submit_payment/unlock_cert
  uroven           text NOT NULL DEFAULT 'batch',     -- batch/event
  actor            text,                              -- user/marti-ai/claude
  vysledek         text,
  detail           jsonb,
  created_at       timestamptz NOT NULL DEFAULT now()
);

-- GRANTy pro strategie (API role) — povinné po DDL na tenant.*
GRANT SELECT,INSERT,UPDATE,DELETE ON
  tenant.bank_provider, tenant.bank_connection, tenant.bank_connection_account,
  tenant.bank_transaction_raw, tenant.bank_payment_order, tenant.bank_api_log
  TO strategie;
GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA tenant TO strategie;

-- Seed prvního providera  [review #6: reálná RB base]
INSERT INTO tenant.bank_provider (kod,nazev,base_url,auth_typ,schopnosti)
VALUES ('RB_PREMIUM_API','Raiffeisenbank Premium API','https://api.rb.cz/rbcz/premium/v2','cert_mtls',
  '{"statements":true,"transactions":true,"balances":true,"payments":true}'::jsonb)
ON CONFLICT (kod) DO NOTHING;
