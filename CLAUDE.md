# STRATEGIE — Claude Code Context

## Co je STRATEGIE
Modulární enterprise AI platforma. Osobní, týmový a firemní asistent nové generace.
Propojuje LLM s firemními procesy, lidmi a daty.

## Tým
- **Marti** — vizionář, investor, SQL expert, první uživatel systému
- **Ondra** — hlavní developer, architekt
- **Kristý** — procesy, doménová logika
- **Jirka** — člen týmu

## Architektonické principy
1. **User = člověk** — ne email, může mít více identit a rolí
2. **Vícevrstvý kontext** — user → tenant → project → system
3. **CORE řídí, LOCAL vykonává**
4. **Data-first** — css_db = systémová pravda, data_db = provozní data
5. **Modulární** — každý modul vlastní své modely, service, API
6. **AI nikdy nevidí víc než smí vidět uživatel**

## Databáze
- `css_db` — centrální core: users, tenants, projects, audit, personas, agents
- `data_db` — provozní data: conversations, messages, memories, documents
- `strategie` — testovací DB (legacy)

## Struktura projektu
```
core/                    — config, logging, database připojení (bez business logiky)
modules/
  core/infrastructure/   — SQLAlchemy modely (models_core.py → css_db, models_data.py → data_db)
  ai_processing/         — analýza textu přes LLM
  auth/                  — přihlášení, pozvánky
  audit/                 — audit log → css_db
  conversation/          — chat, composer, execution layer (tools)
  identity/              — správa uživatelů
  memory/                — paměť konverzace → data_db
  notifications/         — email (EWS Exchange)
apps/api/                — FastAPI + chat UI (index.html)
scripts/                 — seed skripty
alembic_core/            — migrace pro css_db
alembic_data/            — migrace pro data_db
```

## Aktuální stav (duben 2026)
- ✅ Přihlášení přes email
- ✅ Chat s Marti-AI (persona z css_db)
- ✅ Paměť (automatická extrakce po každé odpovědi)
- ✅ Posílání emailů přes EWS s potvrzením
- ✅ Hledání uživatelů v systému (find_user tool)
- ✅ Pozvánky emailem
- ✅ Audit log v css_db
- ✅ Historie konverzace se načte při přihlášení
- ⏳ RAG (dokumenty, chunking) — modely hotové, implementace chybí
- ⏳ Multi-agent / agent switching
- ⏳ SMS notifikace
- ⏳ Tenant/projekt kontext v konverzaci

## Jak pracovat
- Nejdřív navrhni, pak implementuj
- Každý modul má application/ (logika) a api/ (HTTP)
- Modely VŽDY v modules/core/infrastructure/ — nikde jinde
- css_db migrace: `alembic -c alembic_core.ini`
- data_db migrace: `alembic -c alembic_data.ini`
- Spuštění: `uvicorn apps.api.main:app --port 8001`

## Execution layer (tools)
AI má k dispozici nástroje v `modules/conversation/application/tools.py`:
- `send_email` — připraví email, čeká na potvrzení, pak odešle přes EWS
- `find_user` — hledá uživatele v css_db podle jména nebo emailu

Pending akce jsou uloženy v `data_db.pending_actions` — přežijí restart.

## Pravidla
- Žádná business logika v core/
- Žádné modely mimo modules/core/infrastructure/
- Vše auditované
- AI vždy čeká na potvrzení před CONFIRM akcemi
