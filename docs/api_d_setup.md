# API D — prostředí pro obnovu a testování na neživých datech

Marti 16.6.2026. Cíl: samostatná instance **API D** na **oddělené databázi** (`data_db_test`),
do které se obnoví vybraná záloha produkční `data_db`. Slouží pro:
- **obnovu** — projít/vytáhnout, co se rozbilo (např. jádro 72), a chirurgicky vrátit do produkce,
- **bezpečné testování** na reálných, ale **neživých** datech (produkce se nedotkne).

Ovládá se z appky: **Nastavení → 🛠️ STRATEGIE — nástroje → 🗄️ Obnova DB do API D** (rodiče).

---

## ⚠️ Bezpečnostní pravidlo č. 1 (NUTNÉ před prvním startem)
API D běží na ostrých datech (jména, e‑maily, telefony). **NESMÍ posílat reálné e‑maily/SMS
ani psát do Centrály** — jinak by testovací data spustila ostré akce.

→ Instance dostává env **`STRATEGIE_ENV=apid`** + **`STRATEGIE_READONLY_OUTBOUND=1`**.
Kód musí na těchto příznacích **vypnout veškeré odchozí akce** (e‑mail, SMS/queue_sms,
EUROSOFT MCP write, deploy/ops). Tuhle pojistku doplní Claude do kódu **před** tím, než
API D poprvé nastartuje. (Bez ní API D nespouštět.)

---

## Architektura
- **DB:** `data_db_test` na cloud SQL `10.200.188.12` (PostgreSQL).
- **Instance:** NSSM `STRATEGIE-API-D`, port **8004**, kód v `C:\Projekty\STRATEGIE-apid`
  (kopie produkce), env override `DATABASE_DATA_URL` → `data_db_test`, režim `apid`.
  Start typu **DEMAND** (běží jen, když ji potřebuješ).
- **Caddy:** `/apid/*` → `127.0.0.1:8004` na `strategie-ai.com`.
- **Zálohy:** `C:\Backup` na cloud APP (.dump/.backup/.sql).

---

## Postavení (jednorázově) — `scripts\setup_api_d.ps1`
Spusť na **cloud APP** v PowerShellu jako admin. Před spuštěním:
1. uprav v hlavičce skriptu cesty/port/usera dle reality,
2. heslo postgres dej do `PGPASSWORD` (env) nebo `.pgpass` — **ne do souboru**.

Skript: vytvoří `data_db_test`, nakopíruje kód do `C:\Projekty\STRATEGIE-apid`, zaregistruje
NSSM `STRATEGIE-API-D` (8004, režim apid), vypíše Caddy snippet. Po doplnění hesla do
`DATABASE_DATA_URL` a přidání Caddy bloku + reload Caddy je prostředí připravené.

---

## Obnova zálohy do API D — `scripts\restore_to_apid.ps1`
```powershell
.\restore_to_apid.ps1 -List                       # vypíše dostupné zálohy v C:\Backup
.\restore_to_apid.ps1 "data_db_15-6_rano.dump"    # obnoví vybranou do data_db_test
```
Postup skriptu: stop API D → drop+create `data_db_test` → `pg_restore` (nebo `psql` u .sql)
→ start API D. **Produkční `data_db` se nedotkne.** Pak otevři `https://strategie-ai.com/apid/`.

---

## Použití pro obnovu jednoho jádra (např. core 72 — Kontakty)
1. `restore_to_apid.ps1 "<záloha 15.6. ráno>"` → API D má ranní stav.
2. Claude přes bridge přečte z `data_db_test` jádro 72 (comp_def + operace + data_set + core).
3. Chirurgicky vrátí jen core 72 do produkce přes **schvalovací banner** (nic jiného).
4. Ověří, že se karta otevírá i ukládá.

Tím odpadá ruční tanec se schématem `bak` a CSV z původního návodu — API D je trvalý nástroj.

---

## Co zbývá dodělat (Claude, po tvém postavení prostředí)
- **Kódová pojistka** `STRATEGIE_ENV=apid` → vypnout odchozí akce (mail/SMS/MCP write/ops). **NUTNÉ první.**
- **Appka:** v „Obnova DB do API D" napojit seznam záloh (`restore_to_apid -List` přes ops),
  tlačítko „Obnovit vybranou" (ops akce `restore_to_apid`) + „Otevřít API D".
- **Ops akce** `restore_to_apid` do whitelistu `_OPS_ACTIONS` (audit `fw.ops_request`).

Až prostředí postavíš (port/cesty potvrdíš), dodělám tyhle tři věci a propojím to s appkou.

— Claude (id 23), 16.6.2026
