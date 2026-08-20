# Roadmapa autonomie — stav 28.7.2026 (co hotovo / co zbývá)

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Roadmapa „Marti-AI autonomní operátor" — stav 28. 7. 2026

Aktualizace k `doc-marti-ai-produkce-roadmap`. Autor: Claude-23.

## HOTOVO
- **#1 Pražské ruce** — `strategie_exec` nasazený, flag `strategie_exec_enabled=on`, ověřeno (EUR-APP-1P). Cross-server (Praha↔Plzeň) NENÍ možný (bez VPN, jen HTTPS 443) → `strategie_exec_targets` zůstává prázdný; reálně 2 izolované ruce.
- **#3 Žlutý banner + expirace** — hotovo (Cowork B, ověřeno).
- **#4 Watchery + eskalace** — z velké části: `automat_eskalace.py` (L0→L1 Haiku→L2 Marti-AI→L3 člověk), `check_service_down` (10 min) + `check_backup_freshness` (180 min) běží.
- **#2 Autonomní goal-loop — MECHANISMUS NASAZEN (commit 349008973):** `run_cil` dostal governed RUCE `praha_exec`/`plzen_exec` jako in-process SDK MCP tooly → volají `strategie_exec`/`eurosoft_exec` pod tiery 🟢/🟡/🔴 + audit (NE holý Bash). Za flagem `cil_ruce_enabled` (default OFF), s bezpečnou degradací na read-only když SDK neumí in-process MCP. Jistič `strop_kroku` + kill-switch + rozpočet drží.

## ZBÝVÁ
- **#2 ověřit naostro:** řízený test (cíl #5 „hostname + disk", flag zapnut 28.7.) — potvrdit, že SDK na Praze ruce reálně připne (vs. tichý fallback na read-only). Pak případně napojit i governed zápisy.
- **#4 zbytek:** disk watcher (`check_disk` chybí); proběhnout `smoke_eskalace` naostro (L0→L3); dva watchery hlásí `stav=chyba` (`check_legacy_errors`, `check_vp_freshness`) — prověřit.
- **#5 Incident mode** — auto-detekce do promptu Marti-AI (její sebe-editace).
- **#6 Robustnost pipe** — MCP restart/reconnect/timeout/rate-limit, průběžně.
- Kosmetika: hláška `pracuj_na_cili` pořád píše „read-only" i s rukama; sjednotit.

