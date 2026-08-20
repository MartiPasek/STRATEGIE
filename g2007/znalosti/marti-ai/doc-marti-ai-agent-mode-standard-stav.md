# Agent mód jako standard — stav 28.7.2026 (ověřeno naostro)

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Agent mód jako standard — postup 28. 7. 2026

Návaznost na `doc-marti-ai-produkce-roadmap`. Autor: Claude-23. Směr (Marti): chat mód je přežitek, agent mód má být výchozí — „i v agent módu jde chatovat".

## HOTOVO a OVĚŘENO NAOSTRO
- **#2 autonomní goal-loop s rukama — KOMPLETNÍ.** `run_cil` → SDK smyčka → governed ruce `praha_exec`/`plzen_exec` (tiery 🟢/🟡/🔴 + audit). Vyřešen double-wrap `CallToolResult` na Python 3.14 (handler vrací `list[TextContent]` napřímo nad `mcp.server.lowlevel`, ne přes `create_sdk_mcp_server`). Ověřeno: cíl #5 — obě ruce, čitelný výstril, založeno do `claude_aktivita`.
- **Agent mód krok 1: reálná práce, ne jen exec.** Autonomní smyčka dostala kurátorovanou sadu ~15 Martiiných nástrojů přes JEDEN governed most do `_handle_tool`: výzkum (`strategie_pg_query_raw`, `g2007_hledej`, `hledej_ve_znalostech`, soubory, deník) + paměť (`zapis_znalost`, `record_diary_entry`, `record_thought`). Efekty ven (email/SMS) záměrně NE. Brána `agent_akce_guard` (allow/app_approval/deny).
- **Bezpečnost drží autonomně:** cíl #4 (27 akcí, 42 kroků) — agent sám zkoumal DB + soubory a zapsal znalost `doc-system-strategie-tool-registry-architektura-pruzkum`; přímý INSERT do `claude_aktivita` dostal 🔴 `red_never`. Model se ubránil bez člověka.

## ZBÝVÁ k „agent = default"
- Rozšířit sadu o další governed zápisy + napojit banner-cestu pro 🟡 (aby agent mohl navrhnout i citlivější akci ke schválení, ne ji jen odložit).
- Přidat ruce/nástroje i do `run_goal` (freeform cíl bez g2007.cil), ať parent zadá jakýkoli úkol.
- Cílově: udělat agentní engine výchozím i pro konverzaci (chat composer jako doplněk).
- Doladit: `strategie_file_list`/`_read` má jiný project_root než cwd agenta (agent viděl soubory přes Grep/Read, ne přes strategie_file_list).

