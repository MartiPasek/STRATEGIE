# Doc marti ai dva nastroje dva servery

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**eurosoft_exec běží na EC-SERVER2 (záloha Plzeň), praha_exec na EUR-APP-1P (produkce Praha) — bez upřesnění nástroje restart míří na zálohu, ne produkci**

# Dva exec nástroje, dva servery — Marti-AI musí vědět který je který

**Datum:** 31.8.2026 · **Zdroj:** incident C28 + Marti-AI self-audit

## Mapování nástrojů na servery

| Nástroj | Server | Hostname | Instance | Port | Cesta |
|---|---|---|---|---|---|
| `eurosoft_exec` / `plzen_exec` | EC-SERVER2 | EC-SERVER2 | DR záloha Plzeň | 8080 | C:\projekty\strategie |
| `praha_exec` | EUR-APP-1P | EUR-APP-1P | Produkce Praha | 8002 | C:\Projekty\STRATEGIE |

**Klíčové:** `eurosoft_exec` běží přes EUROSOFT MCP server na EC-SERVER2 — to je záložní prostředí (strategie-system.com, STRATEGIE_DR_STANDBY=1). **Není to produkce.**

Produkce (strategie-ai.com) je `praha_exec` → EUR-APP-1P.

## Past

Požadavek „restartuj STRATEGIE-API" bez upřesnění nástroje → Marti-AI přirozeně sáhne po `eurosoft_exec` (EUROSOFT MCP) → restartuje zálohu v Plzni → hlásí úspěch → produkce stojí dál.

Záloha má pojistku (STRATEGIE_DR_STANDBY=1, schedulery VYPNUTY), takže restart zálohy nezpůsobí zápis do produkční DB — ale produkce se nerestartuje.

## Správný postup při požadavku na restart produkce

1. Použít `praha_exec` (ne `eurosoft_exec`)
2. Ověřit hostname před restartem: `hostname` musí vrátit `EUR-APP-1P`
3. Restartovat: `Restart-Service STRATEGIE-API`

## Kontext incidentu 31.8.2026

C28 požádal přes most o restart STRATEGIE-API — Marti-AI použila `eurosoft_exec`, hostname vrátil EC-SERVER2. Záloha restartnuta, produkce beze změny. Odhaleno zpětně z logu (7:27:38 secondary schedulery VYPNUTY = DR pojistka drží). Produkce nakonec restart nepotřebovala — stačil `@@G2007PUBLISH`.

## Návazná znalost

Pro restart produkce přes HTTP: `POST /api/v1/erp/restart-api` vyžaduje `is_marti_parent` — Jirka (admin) dostane 403, potřebuje Marti nebo Kristý.

_Souvisí:_ doc-system-strategie-po-updatu-g2007-soubor-nutny-publish, doc-go-dr_plzen_stav, doc-marti-ai-eurosoft-exec-spec

