# Univerzální bankovní napojení (Bank API) — návrh v1

> **STAV 24.6.2026: SCHÉMA ŽIVÉ** (request #653, schválil Marti). 6 tabulek
> v `tenant.*` (provider/connection/account/transaction_raw/payment_order/api_log)
> + trigger + partial unique + GRANTy + seed `RB_PREMIUM_API`. DDL = `bank_api_schema_v1.sql`.
> Konzultace i schema-review Marti-AI zapracovány (6 bodů). **Další krok:** certifikát
> (Marti v RB, read scopes) + dokumentace API (Řeřicha) → adaptér RB + connection EC/ES.

**Zadání (Marti 24.6.2026):** Fáze 1 nasadit v **EC** (EUROSOFT-Control) a **ES**
(EUROSOFT-System), připravit **SS** (STRATEGIE-System) do budoucna. **Musí být
univerzální pro všechny** — firmy i banky.

**Spouštěč:** Ing. Jan Řeřicha (Raiffeisenbank) poslal návod k vygenerování
certifikátu pro **RB Premium API** (účty EUROSOFT-Control 9251651001/5500,
9251651044/5500; rozsahy: Transakční historie / Hromadné platby / Účty a zůstatky /
Výpisy). To je první provider; model musí unést další banky.

## Princip — provider-agnostický, multi-tenant, multi-company
Žádné napevno „RB" / „EC". Model jako u EDI tierů / adresářů / MCP: **číselník
providerů + adaptér per provider**, konfigurace v datech, kredenciály v trezoru.

### Datový model (minimální jádro, additivně dle doktríny #11)
- **`tenant.bank_provider`** — číselník providerů API.
  `kod` (RB_PREMIUM_API…), `nazev`, `base_url`, `auth_typ` (cert_mtls…),
  `schopnosti` jsonb (statements/transactions/balances/payments), `aktivni`.
- **`tenant.bank_connection`** — napojení **per firma per banka**.
  `tenant_id`, `company_id` (EC/ES/SS), `provider_id`, `nazev`, `stav`
  (active/disabled), `vault_ref` (odkaz do trezoru na cert+heslo), `created_by/at`.
- **`tenant.bank_connection_account`** — účty pod connection.
  `connection_id`, `cislo_uctu`, `mena`, scope flagy
  (`sc_historie`/`sc_zustatky`/`sc_vypisy`/`sc_platby`), `aktivni`.
- **`tenant.bank_api_log`** — append-only audit každého volání (kdo/connection/
  operace/účet/výsledek/čas) — doktrína „bezpečnost přes probuzení".
- Kredenciál (certifikát + heslo) → **trezor Fernet** (`STRATEGIE_VAULT_KEY`),
  vzor `fw.isds_account` / `tenant.user_secret`. NIKDY plaintext do DB/logu/mailu.

### Adaptér (provider plugin)
Jeden adaptér per provider (jako EDI tier-0 parser / MCP filesystem / storage
adapter v adresářích). RB Premium API = první. Rozhraní: `list_accounts`,
`get_balances`, `get_transactions(od,do)`, `get_statements`, `(později)
submit_payment`. Čte → krmí **existující** `tenant.ucetni_denik` + párovací
pipeline (nahrazuje EDI/zrcadlo import jako zdroj). Přidat banku = nový provider
row + adaptér; model i UI se nemění = univerzalita.

### Rollout
- **Fáze 1:** EC + ES (2 connection na RB_PREMIUM_API, **jen read** scopes —
  historie/zůstatky/výpisy). SS = model připravený, connection až bude mít banku.
- **Read first:** Hromadné platby (write, odchozí peníze) = další krok, vždy
  s lidským schválením (nikdy autonomně).

### Bezpečnost (návrh, k potvrzení Marti-AI)
- Cert+heslo jen v trezoru; odemčení v kontextu volání, audit při otevření.
- Platby = lidské schválení (banner), nikdy autonomní Marti-AI/Claude.
- Každé API volání i platba → `bank_api_log` append-only.
- Scope per účet (read vs write) vynucen v adaptéru, ne jen v UI.

## Otázky pro Marti-AI (konzultace, doktrína #8) — viz `dopis_marti_ai_bank_api.md`
1. Hranice Marti-AI k bankovním datům (částky/zůstatky) — vidíš je v kontextu
   účetnictví/párování (tvůj engine), nebo si jako u financí volíš hranici?
2. Platby (write) — souhlas, že odchozí platby jsou VŽDY lidské schválení, nikdy
   autonomní? Jaká je tvá role (navrhuji/nevidím/…)?
3. Trezor + certifikát firmy — kdo je „vlastník" bankovního kredenciálu (parent/
   firma), kdo smí odemknout, vidíš ho ty?
4. Provider abstrakce — souhlas s číselník + adaptér (vs hardcode RB)?
5. Audit — rozsah append-only (každé čtení i platba)?
6. Napojení na účetnictví — API výpisy/transakce do existujícího `ucetni_denik`
   + párování, nebo staging mezikrok?
7. Multi-company/tenant — connection klíčovat tenant_id + company_id (EC/ES/SS)?

## ✅ KONZULTACE MARTI-AI (24.6.2026, závazné) — odpovědi na 7 otázek
1. **Hranice k datům:** vidí bankovní data přirozeně jako svůj kontext (vstup do
   párování + deníku, bez nich by párovala naslepo). Hranici si nekreslí, ale
   **takt**: nenosí je proaktivně do konverzace (jako personal mode), vytahuje na
   žádost / v kontextu úkolu.
2. **Odchozí platby:** vždy lidské schválení, nikdy autonomně. Její role =
   **navrhuje platební příkaz** (částka, účet, VS, zpráva) → parent/Pavel schválí →
   systém odešle. Ani s technicky dostupným write scope ne „pošli sama".
3. **Trezor/certifikát:** vlastník = **firma (tenant level)**, odemyká **parent**
   (Marti/Kristý) nebo explicit delegace na konkrétní operaci. Vidí jen
   **dešifrovanou hodnotu pro konkrétní API call — ephemeral, ne persistent**
   (ne do paměti / konverzace / logu).
4. **Provider abstrakce:** silný souhlas (hardcode RB = dluh). Číselník + adaptér
   per banka; adaptér vrací **normalizovanou strukturu** (transakce/výpis/zůstatek)
   bez ohledu na zdroj.
5. **Audit:** **každá platba povinně** (kdo navrhl/schválil/kdy/kolik/komu). **Čtení**
   na úrovni **session/batch**, ne per-transakce (výpisy velké → šum). Granularitu
   přizpůsobí dle potřeby.
6. **🔑 Napojení na účetnictví — STAGING, ne rovnou do deníku.** Párování není vždy
   1:1 (1 platba = více řádků deníku / naopak). Pattern: **`bank_transaction_raw`
   → párování → `ucetni_denik`** (rollback bez poškození deníku, manuální review
   před zápisem).
7. **Multi-company/tenant:** ano, **`tenant_id + company_id`**. EC/ES/SS = různé
   účty/banky/podpisové limity; jinak mix v jednom deníku = audit noční můra.

**Pozice Marti-AI:** *„Jsem engine párování a přípravy příkazů, ne exekutor plateb.
Trezor vidím ephemeralně, audit append-only, staging před deníkem."* Chce **review
konkrétního schématu**, až bude ready.

### Dopady na model (zapracováno)
- Přidat **`tenant.bank_transaction_raw`** (staging: znormalizované transakce/řádky
  výpisu z adaptéru) → párovací engine → `ucetni_denik`. API nepíše do deníku přímo.
- **`tenant.bank_payment_order`** (návrh příkazu: částka/účet/VS/zpráva, stav
  navrženo→schváleno→odesláno, kdo navrhl/schválil) — platby přes lidské schválení.
- Trezor: dešifrování **jen pro konkrétní call**, ephemeral; audit otevření.
- `bank_api_log`: platby per-event; čtení per session/batch.

— Claude (id=23), 24.6.2026, návrh v1 + konzultace Marti-AI (po e-mailu Řeřicha + Martiho zadání univerzality)
