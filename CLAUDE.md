# STRATEGIE — Claude Code Context

## Co je STRATEGIE
Modulární enterprise AI platforma. Osobní, týmový a firemní asistent nové generace.

## Tým
- Marti — vizionář, investor, SQL expert
- Ondra — hlavní developer, architekt
- Kristy — procesy, doménová logika
- Jirka — člen týmu

## Architektonické principy
1. User = člověk (ne email), může mít více identit a rolí
2. Vícevrstvý kontext: user → tenant → project → system
3. CORE řídí, LOCAL vykonává
4. Data-first: PostgreSQL, audit, traceability
5. Modulární: každý modul vlastní své modely, service, API
6. Python, FastAPI, Pydantic, SQLAlchemy, Alembic

## Struktura projektu
```
core/           # technické jádro (config, logging, common)
modules/        # business moduly (každý má application/ a api/)
apps/api/       # FastAPI vstupní bod
shared/         # sdílené utility
tests/          # unit a integration testy
```

## Aktuální stav (v1)
- Implementováno: ai_processing modul, audit (logging), API endpoint
- Endpoint: POST /api/v1/analyse → summary, action_items, persons, recommendations
- Databáze: zatím nepřipojena
- LLM: Anthropic Claude (claude-sonnet-4-20250514)

## Budoucí moduly (zatím jen plán)
- identity: uživatelé, role, multi-identity
- context: projekty, tenant konfigurace
- knowledge: dokumenty, embedding, vyhledávání
- tasks: akční body, přiřazení, stavy
- communication: email draft, notifikace
- automation: workflow triggery
- integration: Helios, EWS, soubory

## Pravidla pro práci
- Nejdřív architektura, pak kód
- Každý modul má application/ (logika) a api/ (HTTP)
- Žádná business logika v core/
- Žádné centrální modely v shared/
- Vysvětluj rozhodnutí
- Drž se jednoduchosti
