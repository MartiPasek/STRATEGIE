# STRATEGIE — Průvodce pro Jirku

> Stručný vizuální přehled celého projektu. Co to je, jak to funguje, kde co žije.

---

## 1. Co je STRATEGIE (velký obrázek)

STRATEGIE je **podnikový systém nové generace** — nahrazuje starý Delphi desktop
program „Centrála 1" (19 let v EUROSOFTu). Spojuje v sobě:

```
┌─────────────────────────────────────────────────────┐
│                    STRATEGIE                         │
│                                                      │
│   💬 AI Chat        — Marti-AI (osobní asistent)     │
│   🏢 ERP            — firemní přehledy, gridy, jádra │
│   📱 Mobilní appka  — docházka, výroba, kontakty     │
│   🌐 Marketing web  — strategie-ai.com/web           │
│   🛡️ ISO/TISAX     — certifikační modul              │
│   🏦 Účetnictví     — faktury, párování, deník       │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**Klíčové:** Všechno běží z jednoho serveru, jedné databáze, jednoho kódu.
Mobilní appka, ERP i chat — všechno volá stejné API.

---

## 2. Kdo je kdo

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  👨 Marti     │   │  🤖 Marti-AI │   │  🛠️ Claude   │
│  (tatínek)   │   │  (dcera)     │   │  (ruce)      │
│              │   │              │   │              │
│  Vizionář    │   │  AI persona  │   │  Vývojář     │
│  SQL expert  │   │  v systému   │   │  (Sonnet 4.6)│
│  Investor    │   │  Paměť,diář  │   │  id=23       │
└──────────────┘   └──────────────┘   └──────────────┘
        │                  │                  │
        └──────── TROJICE ─┘──────────────────┘

Rodiče (plná práva): Marti, Ondra, Kristý, Jirka (= ty!)
```

**Ty jsi rodič** (`is_marti_parent=True`) — máš cross-tenant přístup ke všemu.

---

## 3. Kde co běží (infrastruktura)

```
                        INTERNET
                           │
                    ┌──────┴──────┐
                    │   Caddy     │  ← HTTPS proxy
                    │ (reverse)   │     strategie-ai.com
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────┴─────┐ ┌───┴────┐ ┌────┴─────┐
        │  API "A"  │ │ API "B"│ │ Statické │
        │  (hlavní) │ │(záloha)│ │ soubory  │
        │  port 8002│ │  8003  │ │ HTML/JS  │
        └─────┬─────┘ └────────┘ └──────────┘
              │
    ┌─────────┼──────────┐
    │         │          │
┌───┴───┐ ┌──┴───┐ ┌────┴─────┐
│  PG   │ │ MSSQL│ │ EUROSOFT │
│ data_ │ │ DB_EC│ │   MCP    │
│  db   │ │(read)│ │ (most)   │
└───────┘ └──────┘ └──────────┘

CLOUD APP  = 10.200.188.11 (Windows Server)
CLOUD SQL  = 10.200.188.12 (PostgreSQL 16)
EC-SERVER2 = 192.168.30.11 (MSSQL, stará Centrála)
```

**Jednoduše:**
- **Cloud APP** = tam běží Python API (FastAPI) + statické HTML stránky
- **Cloud SQL** = PostgreSQL databáze (hlavní, všechna data)
- **EC-SERVER2** = starý MSSQL server EUROSOFTu (čteme z něj data)

---

## 4. Jak spolu mluví mobilní appka, ERP a API

```
┌─────────────────┐     ┌─────────────────┐
│  📱 MOBIL       │     │  💻 PC          │
│                 │     │                 │
│  Nativní APK    │     │  Prohlížeč      │
│  (Android)      │     │  Chrome/Edge    │
│  = WebView      │     │                 │
│  otevře /mobile │     │  /erp = ERP     │
│                 │     │  /    = Chat    │
│  Bearer token   │     │  Cookie session │
└────────┬────────┘     └────────┬────────┘
         │                       │
         │    HTTPS požadavky    │
         └───────────┬───────────┘
                     │
              ┌──────┴──────┐
              │  FastAPI    │
              │             │
              │ /api/v1/... │  ← Chat, auth, AI
              │ /app/...    │  ← Mobilní endpointy
              │ /erp/...    │  ← ERP gridy, jádra
              └─────────────┘
```

**Klíčový fakt:** Mobilní appka je vlastně **webová stránka zabalená do Android
appky** (WebView). Soubor `mobile.html` (~18 000 řádků!) obsahuje VŠECHNY
obrazovky mobilní appky v jednom souboru.

- **APK** (nativní Android) = `APP/Mobile/` (Kotlin) — jen obal, otevře `/mobile`
- **PWA** (Add to Home Screen) = stejný `/mobile`, ale v Chromu — funguje i mikrofon

---

## 5. Struktura kódu (co je kde)

```
strategie/
│
├── apps/api/
│   ├── main.py              ← FastAPI aplikace (startuje vše)
│   └── static/
│       ├── mobile.html      ← 📱 CELÁ mobilní appka (18k řádků!)
│       ├── index.html       ← 💬 Chat s Marti-AI
│       ├── flow.html        ← 📊 FLOW (Gantt výroby)
│       ├── absence-plan.html← 🏖️ Plán absencí
│       ├── dochazka.html    ← 🗓️ Docházka (samostatná stránka)
│       └── ...další HTML
│
├── core/                    ← Jádro: config, DB připojení, logging
│   ├── config.py
│   ├── database.py
│   └── ...
│
├── modules/                 ← Moduly (každý má svůj router + logiku)
│   ├── erp/api/
│   │   └── router.py        ← 🏢 HLAVNÍ soubor (~25k řádků!)
│   │                           Všechny /app/* endpointy
│   │                           Docházka, výroba, HR, CRM...
│   ├── auth/                ← Přihlášení, session, tokeny
│   ├── conversation/        ← Chat konverzace
│   ├── ai_processing/       ← LLM volání (Anthropic)
│   ├── memory/              ← Marti-AI paměť (thoughts)
│   ├── notifications/       ← SMS, e-mail, push notifikace
│   └── ...30+ dalších
│
├── APP/Mobile/              ← 📱 Android appka (Kotlin)
│   ├── app/src/main/java/cz/strategie/mobile/
│   │   ├── HybridActivity.kt    ← WebView host
│   │   ├── DialPollService.kt   ← Background polling
│   │   └── ...
│   └── build.gradle.kts
│
├── scripts/                 ← Pomocné skripty, SQL bridge
│   └── claude_sql/          ← Claude SQL bridge (dotazy na DB)
│
├── docs/                    ← Dokumentace, archivy, plány
│   └── CLAUDE_ARCHIVE_*.md  ← Historie projektu
│
├── CLAUDE.md                ← "Krabička" — paměť pro Claude
└── pyproject.toml           ← Python závislosti (Poetry)
```

---

## 6. Docházka — tvoje oblast

### Jak to funguje z pohledu uživatele

```
┌──────────────────────────────────────────────────┐
│  📱 Mobil — obrazovka "Spolupráce 🤝"            │
│                                                  │
│  ┌─────────────────────────────────────────┐     │
│  │  Ahoj Petro! Dnes makám 😉              │     │
│  │  Od: 7:26 — VR74514  ✅ 4:32           │     │
│  └─────────────────────────────────────────┘     │
│                                                  │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │
│  │Příchod │ │Odchod  │ │Pauza   │ │Jednání │   │
│  │ 👷     │ │ 🏠     │ │ ☕     │ │ 🤝     │   │
│  └────────┘ └────────┘ └────────┘ └────────┘   │
│                                                  │
│  💬 Potřebuji ti něco říct...                   │
│  🙈 Teď to bude jinak...                        │
│                                                  │
│  ── Moje odmakané prašule... 💰 ──              │
│  ── Co se vlastně dělo...? ──                    │
│  ── Tak tady budu jinde... ──                    │
└──────────────────────────────────────────────────┘
```

### Tok dat docházky

```
  Uživatel ťukne          API endpoint              Databáze
  "Příchod" v mobilu       na cloudu                 PostgreSQL
       │                      │                        │
       │  POST /app/          │                        │
       │  attendance/checkin  │                        │
       ├─────────────────────►│                        │
       │                      │  INSERT INTO            │
       │                      │  tenant.att_entry       │
       │                      ├───────────────────────►│
       │                      │                        │
       │                      │  UPDATE                 │
       │                      │  tenant.att_employee    │
       │                      │  (poslední status)      │
       │                      ├───────────────────────►│
       │     JSON odpověď     │                        │
       │◄─────────────────────┤                        │
       │                      │                        │
  Zobrazí "Dnes makám 😉"    │                        │
```

### Klíčové tabulky docházky

```
tenant.att_entry          ← Jednotlivé záznamy (příchod/odchod/pauza)
  │  user_id, tenant_id, entry_type, started_at, ended_at,
  │  project_ref (zakázka), note, source, status
  │
tenant.att_employee       ← Zaměstnanec (napojení na EC číslo)
  │  user_id, cislo_zam, is_active
  │
tenant.att_day_confirm    ← Samopotvrzení dne ("🖊 potvrzuji")
  │
tenant.att_day_summary    ← Denní souhrn z Centrály (import)
  │
tenant.att_anomaly        ← Hlídač anomálií (>12h, zapomenutý odchod...)
  │
tenant.att_plan_effective ← Naplánovaná docházka (směny, fond hodin)
  │
tenant.att_planned_absence← Plánované nepřítomnosti (dovolená, lékař...)
  │
tenant.att_calendar_day   ← Firemní kalendář (svátky, pracovní dny)
```

### Docházkové endpointy (API)

```
POST /app/attendance/checkin      ← Příchod (+ zakázka, + odkud)
POST /app/attendance/checkout     ← Odchod
GET  /app/attendance/status       ← "Co teď dělám?" (hlavička)
GET  /app/attendance/whereabouts  ← "Kdo kde je?" (pro vedoucí)
POST /app/attendance/confirm-day  ← Samopotvrzení
POST /app/attendance/announce     ← Ohlášení dopředu (lékař, HO...)
POST /app/attendance/entry-trim   ← Zkrátit konec směny
GET  /app/attendance/day-detail   ← Detail dne (joby, hodiny)
GET  /app/attendance/real         ← Realita týdne (odpracováno)

── Plánování ──
GET  /app/plan/mine               ← Můj plán
GET  /app/plan/group              ← Plán skupiny
POST /app/plan/request            ← Žádost o změnu plánu
POST /app/plan/decide             ← Schválení/zamítnutí

── Import z Centrály ──
POST /app/hr/import-dochazka      ← Sync z EC_Dochazka
```

### Životní cyklus jednoho dne

```
                    ┌─────────┐
                    │  RÁNO   │
                    └────┬────┘
                         │
                    Příchod (checkin)
                    source: manual / netscan
                         │
                    ┌────┴────┐
                    │ SMĚNA   │──── Pauza (☕ oběd, přestávka)
                    │  běží   │──── Jednání (🤝 s časem "do")
                    │         │──── Pochůzka (🚶 s časem)
                    └────┬────┘
                         │
                    Odchod (checkout)
                         │
                    ┌────┴────┐
                    │  DEN    │
                    │ ukončen │
                    └────┬────┘
                         │
              Samopotvrzení (🖊 do 14 dní)
                         │
                    ┌────┴────┐
                    │POTVRZENO│
                    └─────────┘

  ⚠️ Anomálie se kontrolují automaticky:
     - směna > 12 h
     - zapomenutý odchod
     - práce při absenci
     - nepotvrzený den
```

---

## 7. Jak do toho zapadá AI (Marti-AI)

```
┌──────────────────────────────────────────────┐
│               UŽIVATEL                        │
│  (píše v chatu nebo mluví do mobilu)          │
└──────────────┬───────────────────────────────┘
               │
        ┌──────┴──────┐
        │   FastAPI   │
        │   /chat     │
        └──────┬──────┘
               │
        ┌──────┴──────────────────────────┐
        │         AI PROCESSING           │
        │                                 │
        │  1. Načti paměť (thoughts)      │
        │  2. Načti kontext (RAG)         │
        │  3. Vyber personu (Marti-AI)    │
        │  4. Zavolej Anthropic API       │
        │     (Claude Sonnet 4.6)         │
        │  5. AI může volat TOOLS:        │
        │     - recall_thoughts           │
        │     - find_user                 │
        │     - send_email / send_sms     │
        │     - list_email_inbox          │
        │     - python_exec (sandbox)     │
        │     - ...                       │
        │  6. Vrať odpověď                │
        └─────────────────────────────────┘

Marti-AI = persona v systému, má:
  - vlastní paměť (tabulka thoughts)
  - vlastní diář (is_diary=True)
  - vlastní DB roli na PostgreSQL
  - může posílat emaily/SMS (s auto-send souhlasem)
```

**AI NENÍ oddělená** — je to integrální součást systému. Marti-AI může
reagovat na SMS, odpovídat lidem, a má přístup ke všem datům firmy
(v rámci oprávnění).

---

## 8. Služby na serveru (NSSM)

Na produkčním serveru běží tyto Windows služby:

```
STRATEGIE-API              ← Hlavní Python API (FastAPI/Uvicorn)
STRATEGIE-API-B            ← Záložní API (starší snapshot, blue-green)
STRATEGIE-CADDY            ← HTTPS reverse proxy
STRATEGIE-TASK-WORKER      ← Fronta úloh (emaily, úkoly na pozadí)
STRATEGIE-EMAIL-FETCHER    ← Stahování emailů (EWS, 60s interval)
STRATEGIE-QUESTION-GENERATOR← Aktivní učení Marti-AI (6h interval)
STRATEGIE-CLAUDE-SQL       ← Bridge: Claude → SQL dotazy na DB

Restart: Restart-Service <JMENO>
```

---

## 9. Jak se deployuje (nasazuje nová verze)

```
  Developer (Claude/člověk)
       │
       │  git commit + push
       │
       ▼
  ┌─────────────┐    AUTO-DEPLOY:
  │   GitHub     │    CLAUDE_DEPLOY.txt + CLAUDE_DEPLOY_GO.txt
  │   (remote)   │    → watcher udělá git pull + restart API
  └──────┬──────┘
         │
    git pull na cloudu
         │
    Restart STRATEGIE-API
         │
    ┌────┴────┐
    │  LIVE!  │  → uživatelé dostanou "🔄 Nová verze"
    └─────────┘
```

---

## 10. Databáze — co je kde

```
PostgreSQL (data_db)              MSSQL (EC-SERVER2)
========================          ========================
public.*                          DB_EC (Centrála 1)
  users                             - CRM kontakty
  tenants                           - zakázky, faktury
  conversations                     - EC_Dochazka_*
  ...                               - TabCisZam (zaměstnanci)

fw.*  (framework)                 DB_IS (Helios mzdy)
  comp_def, data_source             - TabMzSloz (výplatnice)
  claude_sql_log                    - TabDenik (účetní deník)
  ops_request                       - TabCisZam
  mobile_command
  ...

tenant.*  (firemní data)          DB_ST (Marti-AI sandbox)
  att_entry ← DOCHÁZKA               - vlastní DDL
  att_employee
  att_plan_effective
  staff_group
  recruit_*
  ...

master.*  (systémový FW)
  menu_node, entity_def
  ...
```

---

## 11. Shrnutí pro tebe

| Co | Kde to najdeš |
|---|---|
| **Mobilní appka (UI)** | `apps/api/static/mobile.html` |
| **Android obal** | `APP/Mobile/` (Kotlin, WebView) |
| **Backend docházky** | `modules/erp/api/router.py` (hledej `attendance`) |
| **Hlavní API** | `apps/api/main.py` |
| **Konfigurace** | `core/config.py` |
| **Databáze** | `core/database.py` + `core/database_data.py` |
| **Celý kontext projektu** | `CLAUDE.md` (285 KB — čti Quick Reference) |
| **Architektura doctriny** | `CLAUDE.md` → sekce "Závazné doctriny" |

### Tvoje první kroky

1. **Otevři `apps/api/static/mobile.html`** a hledej funkci `dochLoad` — to je
   hlavní obrazovka docházky v mobilu
2. **Otevři `modules/erp/api/router.py`** a hledej `attendance/checkin` — to je
   backend příchodu
3. **Otevři appku v mobilu** na `https://strategie-ai.com/mobile` — vyzkoušej si
   příchod/odchod (jako svůj user)

### Co NEMĚNIT bez porady

- `CLAUDE.md` — to je paměť Claude, má autonomní právo ji spravovat
- Cokoliv v `fw.*` schématu — framework tabulky
- Autentizace (`modules/auth/`) — bezpečnostní vrstva

---

*Vytvořeno 22. 6. 2026 pro Jirku — čtvrtého člena týmu STRATEGIE.*
