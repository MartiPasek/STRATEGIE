# Setup Claude-27 — tým-instance na sdíleném počítači Marti-AI 🎲

Claude-27 obsluhuje **4 lidi**: Mirek (U22), Zuzka (U6), Míša (U16), Eliška (U34).
Kontext má v `docs/team27/` (Claude27.MD + osobní MD). Tohle je **lidský setup**.

## 1. Stroj + repo
- Sdílený počítač **Marti-AI** (kde běží i CMS / další nástroje).
- `git clone` / `git pull` repo STRATEGIE.
- `scripts/claude_sql/INSTANCE_ID.txt` → obsah **`27`** (rozlišení instance; gitignored).

## 2. Watcher (NSSM služba) — jako Claude-24
- Služba **`STRATEGIE-CLAUDE-SQL`** (watcher `scripts/claude_sql_runner.py`).
- Token `STRATEGIE_DEPLOY_TOKEN` do **AppEnvironmentExtra** (NE Machine env — SCM cache!).
- Watcher posílá heartbeat → v `fw.claude_instance` se objeví řádek **`27 · Tym · <hostname>`**.
- Ověř presence: v ERP/appce „Claude-27" ukáže 🟢 běží.

## 3. Smyčka (jak Claude-27 hraje)
1. **Projede frontu** — `@@Q27 LIST` (přes bridge `db=pg`).
2. Vezme položku → udělá práci → `@@Q27 STATUS <id> in_progress` / `done`.
3. **Pošle člověku e-mail** (oslovení dle osobního MD) — co hotovo + co dál → `@@EMAIL`.
   Když čeká na odpověď: `@@Q27 STATUS <id> waiting_reply`.
4. **Nové požadavky** (z odpovědí lidí / příchozích e-mailů) → `@@Q27 ADD {...}`.
5. Když **dojde fronta nebo spadne** → `@@Q27 SLEEP "hotovo, čekám na Go"`.
   → tím se **Zuzce + Mirkovi pošle slyšitelná notifikace** „🤖 Spusť Clauda-27".
6. Po práci **hlásí nám** (Marti + Claude-23) souhrn vytížení (e-mail / heartbeat work_status).

## 4. Probuzení (Go od Zuzky) ⏰
- Zuzka (U6) je **správce běhu**. Když Claude-27 stojí a má frontu, dostane notifikaci.
- V appce: dlaždice **🤖 Claude-27** → vidí frontu → tlačítko **▶ Go**.
  - „Go" zapíše signál do `fw.claude27_wake`.
- Claude-27 si „Go" vyzvedne přes **`@@Q27 WAKE?`** (vrátí `go:true` + konzumuje signál)
  → projede frontu a pokračuje.
- **Mirek (U22)** dostává tytéž notifikace a může dát Go taky (záloha za Zuzku).

### Jak se „Go" promítne do startu Claude-27
- **Teď (manuální):** Zuzka po notifikaci řekne Claudovi-27 na sdíleném počítači „Go"
  (nebo klikne ▶ Go v appce a poté Claude-27 spustí kdokoli u stroje). Claude-27 si
  ověří `@@Q27 WAKE?` a projede frontu.
- **Cíl (automatika):** watcher instance 27 polluje `fw.claude27_wake` (nezkonzumované
  signály) → na „Go" spustí Claude-27 turn. (Stejný princip jako pollery mostu;
  doladit při setupu — viz `scripts/claude_sql_runner.py`.)

## 5. Bezpečnost (drž)
- Claude-27 **čte sám**, **zápisy do produkce přes schvalovací banner** (rodič) — jako 24/25/26.
- `@@Q27`, `@@EMAIL`, `@@INBOX` běží token-auth (jako Claude-23). Token těsně.
- E-maily lidem autonomně, ale **s úsudkem** — citlivé (peníze, závazky ven) přes člověka.

## 6. Tabulky (už existují, fw.*)
- `fw.claude27_queue` — fronta práce (person_user_id, typ, predmet, status, source_ref).
- `fw.claude27_wake` — budící signály (pressed_by, consumed_at).
- `fw.claude_instance` — presence (řádek instance 27).

## 7. Bridge příkazy (rychlá karta)
```
@@Q27 LIST
@@Q27 ADD {"person":22,"typ":"task","predmet":"Poptávka XY","popis":"…","source":"email#123"}
@@Q27 STATUS <id> in_progress|waiting_reply|done|error
@@Q27 DONE <id>
@@Q27 SLEEP "hotovo, čekám na Go"   ← pošle notifikaci Zuzce+Mirkovi
@@Q27 WAKE?                          ← byl Go? (konzumuje signál)
```

— založil **Claude (id=23)** (ID23), 24.6.2026. Týmová hra. 🐺
