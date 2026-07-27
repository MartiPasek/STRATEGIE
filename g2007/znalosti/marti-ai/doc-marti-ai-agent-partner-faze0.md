# Marti-AI jako autonomní agent-partner — Fáze 0 (vlastní agentí smyčka na Max předplatném)

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Marti-AI jako autonomní agent-partner — Fáze 0

**Stav (23. 7. 2026):** Fáze 0 HOTOVÁ a ověřená naostro. Marti-AI poprvé řídí vlastní agentí smyčku — dostane cíl a sama si přes read-only nástroje (Read/Grep/Glob) proběhne repo a vyrobí analýzu, bez delegace na Claude-23. Motor = Claude Code CLI na Max předplatném, pod její personou (entita id=2).

## Runtime
`modules/conversation/application/martiai_agent_service.py` — zrcadlo `claude_agent_service`, ale s její identitou (system_prompt z `composer.build_prompt`) a jejím kufrem. Vstup `run_goal(goal, requested_by_user_id, conversation_id, allowed_tools)`. Model `claude-sonnet-4-6`, cwd = repo. Z chatu ji spouští meta-nástroj `run_as_agent` (v `tool_registry/handlers.py`), gated flagem.

## Governance a náklady
- Kill switch: `g2007.nastaveni('martiai_agent_enabled')` = on/off (TTL cache 15 s). Nouzový override `MARTIAI_AGENT_ENABLED=1` jen pro testy.
- Rozpočtové brány: per-run 60 Kč, denní 600 Kč (z `g2007.tool_audit`).
- Audit: každý běh → `g2007.tool_audit` akce `agent_run`, actor_entita_id=2.

## AUTH — cesta A = Max předplatné (KLÍČOVÉ)
- Řešení = interaktivní `claude /login` jako Administrator na APP serveru EUR-APP-1P. Uloží OAuth do `C:\Users\Administrator\.claude\.credentials.json` (`subscriptionType=max`). Služby běží jako Administrator → čtou tytéž údaje. ŽÁDNÝ token do `.env`.
- Starý `CLAUDE_CODE_OAUTH_TOKEN` v `.env` byl nesmyslný (nezačínal `sk-ant-oat01-`) → „401 Invalid bearer token". Smazán.
- Agent si při běhu odstraní `ANTHROPIC_API_KEY` z prostředí podprocesu → nemůže spadnout do metered.
- GOTCHA: `cost_usd` je notional (API-ekvivalent ceny), NE účtenka — Claude Code ho vypisuje i na Max předplatném. Nenulové cost ≠ metered. Důkaz předplatného = `subscriptionType=max` + odstranění API klíče, ne cena 0.

## Důkaz (audit agent_run, 23.7.)
4× `false` do ~22:00 (éra špatného tokenu / 401), pak 3× `true` po přechodu na `/login`. Poslední (23:04) spustila Marti-AI sama z chatu — analýza `tool_registry`, 2842 výstupních tokenů.

## Co zbývá
1. PLNÁ IDENTITA (priorita): system_prompt se dnes injektuje zkrácený na ~6000 zn. (Claude Code ho předává přes příkazovou řádku, Windows limit ~32 kB; její plný composer prompt ~100 kB). Vyřešit předání celého promptu jinak (soubor/stdin/SDK setting), ať běží pod kompletní osobností.
2. Pravdivý audit-label (`auth: "unknown"` → „subscription/Max").
3. Hardening: token z `.env` brát jen když začíná `sk-ant-oat01-`.
4. MCP: pro read-only fázi vypnout projektové MCP (`EUROSOFT MCP timeout`).
5. Fáze 1 — goal-loop na pozadí: rozšířit `claude_session_queue` z „otázka→odpověď" na „cíl→dílo". Dnes `run_as_agent` běží synchronně v chatu.
6. Fáze 2 — ruce (`Write`/`Edit`/`Bash`) pod approve (Tool Factory + `deployment_proposals`), deny-list (PowerShell/Cron/tajemství/destrukce).
7. Fáze 3 — autonomie, plánované/samonavržené cíle, poschoďový stroj, fleet.

## Otevřené otázky — stav rozhodnutí
Běží pod personou id=2 (rozhodnuto). Default subscription (rozhodnuto). Spouštěče zatím jen zadané, samonávrhy přes approve (rozhodnuto). Fleet: OTEVŘENO — čeká na ToS.

## Domácí úkoly mimo kód
- ToS u Anthropicu PŘED fleetem (firemní produkce na osobních Max seatech + poolování má podmínky: osobní vs. Team/Enterprise vs. API).
- Náklady na předplatném = usage/rate limit, ne Kč — pro Fázi 1+ přidat awareness usage limitů, ne jen korunové brány.
- Politika Anthropicu (oddělit programmatic do kreditového poolu, ohlášeno 15.6.2026) je POZASTAVENÁ, ne zrušená — může se změnit, nestavět ekonomiku natvrdo na „předplatné navždy pokryje agenty".

