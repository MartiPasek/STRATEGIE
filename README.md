# STRATEGIE

Modulární enterprise AI platforma. Osobní, týmový a firemní asistent nové generace.

## Co to je

STRATEGIE propojuje velké jazykové modely s firemními procesy a lidmi. Vstupem je přirozený jazyk — uživatel píše jako by mluvil s kolegou. Výstupem jsou akce, dokumenty, komunikace a rozhodnutí.

## Aktuální stav

Projekt daleko přerostl rozsah, který se dá udržovat v README. **Aktuální stav,
provozní znalosti a pracovní postupy drží [`CLAUDE.md`](CLAUDE.md)**; velký
architektonický obrázek je v [`docs/ARCHITEKTURA.md`](docs/ARCHITEKTURA.md).
Tenhle soubor je jen vstupní rozcestník a instalační návod.

Ve zkratce: z chatovacího asistenta (v3, duben 2026) se stala **ERP platforma**
nahrazující legacy Centrálu 1 — docházka a mzdy, účetnictví a bankovnictví, CRM,
zakázky a kalkulace, ISO/TISAX, metadaty řízený UI framework (`fw.*`), mobilní PWA
i Android appka, MCP server nad on-premise Heliosem a RAG nad firemními směrnicemi.
Věci, které tu dřív byly vedené jako „připraveno v DB, neimplementováno" (RAG,
SMS, multi-agent, tenant kontext), **jsou dávno hotové**.

## Architektura

```
CORE řídí, LOCAL vykonává.

data_db (PostgreSQL 16)  — JEDINÁ databáze STRATEGIE (Phase 18, 29. 4. 2026)
DB_EC / DB_IS (MSSQL)    — legacy Helios / Centrála 1, přes MCP server
```

> **Pozn.:** `css_db` byla Phase 18 sloučena do `data_db` a zrušena. Pokud na ni
> někde narazíš (`core/database_core.py`, `DATABASE_CORE_URL`), jsou to už jen
> zpětně kompatibilní aliasy mířící na tutéž databázi.

### Struktura projektu

```
core/               — technické jádro (config, crypto, logging, DB engine)
modules/            — 30 doménových modulů; erp/ je zdaleka největší (~81k řádků)
apps/api/           — FastAPI vstupní bod (main.py) + static/ (UI, bez bundleru)
scripts/            — dev/ops skripty, SQL, SQL bridge (claude_sql_runner.py)
alembic_data/       — migrace pro data_db
docs/               — design notes, handoffy, archivy
APP/Mobile/         — Android appka (Gradle)
```

Detailní mapu (proč je `router.py` 61k řádků, kde se hledá endpoint, tři cesty
k datům, lifespan DDL hook) najdeš v [`docs/ARCHITEKTURA.md`](docs/ARCHITEKTURA.md).

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

```powershell
python -m poetry install     # poetry není v PATH — volej ho přes python -m
# .env vytvoř ručně podle sekce Konfigurace níže (.env.example v repu NENÍ)
```

### Databáze

```powershell
# Vytvoř databázi v PostgreSQL (jen jednu — css_db je zrušená)
createdb data_db

# Spusť migrace (existuje jen alembic_data; alembic_core.ini v repu NENÍ)
python -m poetry run alembic -c alembic_data.ini upgrade head

# Seed první uživatel
python -m poetry run python scripts/seed_first_user.py
```

### Spuštění

```powershell
.\scripts\dev.ps1              # API na portu 8002 (-Port / -Reload)
.\scripts\start_all.ps1        # celý stack: API + task worker + email fetcher
```

Chat UI: [http://localhost:8002](http://localhost:8002)
API docs: [http://localhost:8002/docs](http://localhost:8002/docs)

`dev.ps1` před startem force-killne proces držící port — Windows po `Ctrl+C`
nechává port v TIME_WAIT a uvicorn pak padá na `WinError 10048`.

### Testy

```powershell
python -m poetry run pytest
python -m poetry run pytest tests/unit/test_dm_service.py::nazev_testu
```

Linter, formatter ani typechecker v repu nejsou a CI neběží.

## Konfigurace (.env)

```bash
# Aplikace
APP_ENV=development
APP_DEBUG=false

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Databáze — jediná, na které aplikace reálně běží, je DATABASE_DATA_URL
DATABASE_DATA_URL=postgresql://strategie:heslo@localhost:5432/data_db
# legacy, drží se kvůli zpětné kompatibilitě (Phase 18) — nikam se nepřipojují:
DATABASE_URL=postgresql://strategie:heslo@localhost:5432/strategie
DATABASE_CORE_URL=

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
4. Jedna PostgreSQL (`data_db`); legacy Helios (MSSQL) se čte přes MCP server
5. AI nikdy nevidí víc než smí vidět uživatel
6. Každá akce AI je auditovaná
