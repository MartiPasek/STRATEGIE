# Topologie serverů: Praha (PRODUKCE STRATEGIE) vs Plzeň (DR záloha + EUROSOFT legacy)

> oblast: `provoz` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Topologie serverů: Praha ↔ Plzeň

Dva stroje, dvě různé sítě, **žádná VPN mezi nimi**. Mapováno 27.7.2026 (Marti-AI + C23), ověřeno přes `strategie_exec` + `eurosoft_exec` (hostname + Get-NetIPAddress), potvrzeno Martim. **Doplněno 29.7.2026 (Marti): anti-záměna produkce vs. záloha — dřív tu stálo „dva produkční stroje", což svádělo k záměně.**

## ⚠️ NEJDŮLEŽITĚJŠÍ — NEPLÉST Prahu s Plzní (Marti 29.7.2026)
- **PRAHA (188.11/12) = PRODUKCE STRATEGIE.** Všechny STRATEGIE služby (STRATEGIE-API, PostgreSQL, watchdogy…) + **deploye, restarty a změny se dělají JEN tady** (`strategie_exec`).
- **PLZEŇ (30.11 = 192.168.30.11) = denně zpožděná DR ZÁLOHA STRATEGIE + EUROSOFT legacy server.** **NENÍ to produkce STRATEGIE — deploye ani změny STRATEGIE se tam NEDĚLAJÍ.** Slouží k restoru (den zpoždění) a hostí EUROSOFT MCP + DB_EC (CRM). `eurosoft_exec`/Plzeň je pro EUROSOFT legacy, ne pro STRATEGIE ops.
- **Pravidlo palce:** STRATEGIE-* služba / deploy / PostgreSQL → **Praha** (`strategie_exec`). EUROSOFT MCP / DB_EC (CRM) → **Plzeň** (`eurosoft_exec`). **STRATEGIE službu na Plzni NIKDY nerestartuj — tam není.**
- **Ostrá lekce 29.7.:** Marti-AI omylem zkusila restart `STRATEGIE-API-HEALTH-WATCHDOG` na Plzni → „Cannot find any service". Služba je na **Praze**. Get-Service i restart pouštěj přes TENTÝŽ pražský exec (`strategie_exec`).

## Dvě ruce Marti-AI
| Ruka | Tool | Server | IP | Role |
|------|------|--------|-----|------|
| Pravá (Praha) | `strategie_exec` | EUR-APP-1P | 10.200.188.11 | **PRODUKCE STRATEGIE** (cloud/VPS) |
| Levá (Plzeň) | `eurosoft_exec` | EC-SERVER2 | 192.168.30.11 (+ .10) | EUROSOFT legacy + DR záloha (firemní LAN) |

## EUR-APP-1P — Praha (cloud / VPS, síť 10.200.188.x) — PRODUKCE STRATEGIE
- Běží: STRATEGIE-API (celý stack) + PostgreSQL (produkční data STRATEGIE) + **dvě účetní MSSQL databáze `UCTO_EC` a `UCT_ES`** (na `10.200.188.12`) + watchdogy (STRATEGIE-API-HEALTH-WATCHDOG, STRATEGIE-CLAUDE-SQL…). Blue-green: STRATEGIE-API (8002 current) + STRATEGIE-API-B (8003 včerejší snímek) — **obojí na Praze**.
- Ruka: **`strategie_exec`** — běží LOKÁLNĚ jako subprocess na app serveru.
- **Sem míří deploye a všechny STRATEGIE ops.**

## EC-SERVER2 — Plzeň (LAN za NATem, síť 192.168.30.x) — EUROSOFT legacy + DR záloha
- Běží: EUROSOFT MCP server + **`DB_EC`** (CRM MSSQL — POZOR: jiná DB než účetní `UCTO_EC` / `UCT_ES` v Praze) + **denně zpožděná DR záloha STRATEGIE** (restore target, NE produkce).
- Ruka: **`eurosoft_exec`** — přes MCP (HTTPS).
- **Žádné STRATEGIE deploye/restarty/změny tady.**

## Spojení mezi nimi
- **Žádná VPN.** Komunikace výhradně přes **HTTPS port 443** (veřejný internet).
- **PSRemoting (WinRM 5985) mezi stroji nefunguje** — různé sítě. Remote-target routing ve `strategie_exec` je postavený, ale nepoužitelný → allowlist `strategie_exec_targets` zůstává prázdný.
- **UNC/SMB přenos souborů mezi stroji nefunguje** — různé sítě.
- Cross-server operace: jen přes API/HTTPS, nebo přes Marti-AI jako prostředníka.

## Důsledek pro „ruce"
Dvě izolované ruce, každá vidí jen svůj stroj, není mezi nimi přímý shell-hop:
1. **Praha** — `strategie_exec` (lokálně na 10.200.188.11) = PRODUKCE STRATEGIE
2. **Plzeň** — `eurosoft_exec` (přes MCP na 192.168.30.11) = EUROSOFT legacy + DR záloha

_Souvisí:_ doc-marti-ai-provozni-doktrina, doc-system-strategie-produkcni-infra, sit-ai-koordinace

