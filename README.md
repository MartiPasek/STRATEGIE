# STRATEGIE

Modulární enterprise AI platforma. Osobní, týmový a firemní asistent nové generace.

## Co to je

STRATEGIE propojuje velké jazykové modely s firemními procesy a lidmi. Vstupem je přirozený jazyk — uživatel píše jako by mluvil s kolegou. Výstupem jsou akce, dokumenty, komunikace a rozhodnutí.

## Aktuální stav (v3 — duben 2026)

### Co funguje
- Přihlášení přes email
- Konverzace s Marti-AI (persona ze systémového promptu)
- Paměť — AI si pamatuje důležité věci z konverzace
- Posílání emailů přes Exchange (EWS) s potvrzením
- Hledání uživatelů v systému
- Pozvánky nových uživatelů emailem
- Audit log v css_db
- Dvě oddělené databáze: css_db (core) a data_db (data)

### Co je připraveno v DB ale ještě neimplementováno
- Tenant a projekt kontext
- Sdílení konverzací
- Multi-agent (přepínání mezi agenty)
- RAG (dokumenty, chunking, vektory)
- SMS notifikace
- Handoff AI → člověk

## Architektura

```
CORE řídí, LOCAL vykonává.

css_db (DB_Core)     — systémová pravda: users, tenants, projects, audit
data_db (DB_Data)    — provozní data: conversations, messages, memories, documents
```

### Struktura projektu

```
core/               — technické jádro (config, logging, database připojení)
modules/
  ai_processing/    — analýza textu (summary, action items, persons)
  auth/             — přihlášení, pozvánky, onboarding
  audit/            — systémový audit log
  conversation/     — chat, composer, execution layer
  identity/         — správa uživatelů a identit
  memory/           — paměť konverzace
  notifications/    — email (EWS), SMS (připraveno)
  core/             — SQLAlchemy modely pro css_db a data_db
apps/api/           — FastAPI vstupní bod + chat UI
scripts/            — seed skripty
alembic/            — migrace pro strategie DB (testy)
alembic_core/       — migrace pro css_db
alembic_data/       — migrace pro data_db
```

## Technický stack

- Python 3.11+
- FastAPI, Pydantic, SQLAlchemy 2.0, Alembic
- PostgreSQL 16
- Anthropic Claude API
- Exchange Web Services (EWS) pro email

## Tým

- **Marti** — vizionář, investor, SQL expert
- **Ondra** — hlavní developer, architekt
- **Kristý** — procesy, doménová logika
- **Jirka** — člen týmu

## Instalace a spuštění

### Požadavky
- Python 3.11+
- Poetry
- PostgreSQL 16
- Přístup k Anthropic API
- Přístup k Exchange serveru (pro email)

### Instalace

```bash
poetry install
cp .env.example .env
# Vyplň hodnoty v .env
```

### Databáze

```bash
# Vytvoř databáze v PostgreSQL
createdb css_db
createdb data_db

# Spusť migrace
poetry run alembic -c alembic_core.ini upgrade head
poetry run alembic -c alembic_data.ini upgrade head

# Seed první uživatel
poetry run python scripts/seed_first_user.py
```

### Spuštění

```bash
poetry run uvicorn apps.api.main:app --port 8001
```

Chat UI: [http://localhost:8001](http://localhost:8001)
API docs: [http://localhost:8001/docs](http://localhost:8001/docs)

## Konfigurace (.env)

```bash
# Aplikace
APP_ENV=development
APP_DEBUG=false

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Databáze
DATABASE_URL=postgresql://strategie:heslo@localhost:5432/strategie
DATABASE_CORE_URL=postgresql://strategie:heslo@localhost:5432/css_db
DATABASE_DATA_URL=postgresql://strategie:heslo@localhost:5432/data_db

# Exchange (email)
EWS_EMAIL=m.pasek@eurosoft.com
EWS_PASSWORD=...
EWS_SERVER=https://mail.eurosoft.com

# Logging
LOG_LEVEL=INFO
```

## Principy vývoje

1. Nejdřív architektura, pak kód
2. Každý modul má `application/` (logika) a `api/` (HTTP)
3. `core/` neobsahuje business logiku
4. `css_db` = systémová pravda, `data_db` = provozní data
5. AI nikdy nevidí víc než smí vidět uživatel
6. Každá akce AI je auditovaná
