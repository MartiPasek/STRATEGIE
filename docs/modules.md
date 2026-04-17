# STRATEGIE — Plán modulů

Tento dokument popisuje moduly, které budou implementovány v budoucích iteracích.
V1 obsahuje pouze `ai_processing` a `audit`.

## identity
- uživatel jako člověk (ne email)
- více emailů, telefonů, OAuth providerů
- role v rámci tenanta
- vazby na projekty

## context
- tenant / firma
- projekt / doménový kontext
- vícevrstvá izolace dat

## knowledge
- nahrávání dokumentů
- chunking a embedding (pgvector)
- sémantické vyhledávání

## tasks
- akční body z analýzy
- přiřazení uživatelům
- stavy a termíny

## communication
- návrh emailu z analýzy
- notifikace
- šablony

## automation
- workflow triggery
- podmíněné akce
- scheduling

## integration
- Helios ERP (přes MCP stack)
- email (EWS)
- soubory, FTP
- externí API
