# STRATEGIE

Modulární enterprise AI platforma. Osobní, týmový a firemní asistent nové generace.

## Co to je

STRATEGIE propojuje velké jazykové modely s firemními procesy. Vstupem je text (přepis hlasu, poznámky, emaily). Výstupem jsou strukturovaná data — shrnutí, akční body, osoby, doporučení.

## Aktuální stav (v1)

- `POST /api/v1/analyse` — analýza textu přes Claude API
- audit přes logging
- bez databáze, bez autentizace

## Požadavky

- Python 3.11+
- Poetry
- Anthropic API klíč

## Instalace

```bash
poetry install
cp .env.example .env
# Doplň ANTHROPIC_API_KEY do .env
```

## Spuštění

```bash
poetry run uvicorn apps.api.main:app --reload
```

API dokumentace: [http://localhost:8000/docs](http://localhost:8000/docs)

## Struktura projektu

```
core/           # technické jádro (config, logging, common)
modules/        # business moduly (každý má application/ a api/)
apps/api/       # FastAPI vstupní bod
shared/         # sdílené utility
tests/          # unit a integration testy
docs/           # dokumentace a plán modulů
```

## Tým

Marti, Ondra, Kristy, Jirka
