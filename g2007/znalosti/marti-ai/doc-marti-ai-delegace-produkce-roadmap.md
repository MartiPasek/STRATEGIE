# Delegace roadmapy produkce (kdo dělá co)

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Delegace roadmapy „Marti-AI produkčně schopný správce" (27.7.2026)

Roadmapa: `doc-marti-ai-produkce-roadmap`. Paralelizace přes 3 Cowork kanály + Marti-AI.

## Rozdělení
- **C23 (Claude/Cowork, hlavní):** #1 Ruce na Prahu (exec 188.11/188.12), #2 autonomní
  goal-loop (eurosoft_exec do run_cil), #6 robustnost pipe. = exec/loop jádro (sdílený kód,
  kontinuita). Soubory: ops_tools.py, martiai_agent_service.py (run_cil), agent_akce_guard.py,
  eurosoft_mcp_client.py.
- **Cowork instance B:** #3 Žlutý banner + expirace (schvalování 🟡 exec). Kickoff brief
  předán jako soubor. NESAHÁ na exec jádro C23. Endpoint = router.py → koordinace s Peťa/C26.
- **Cowork instance C:** #4 Proaktivní hlídání + eskalační žebřík (automat → Haiku → Claude →
  člověk). Kickoff brief předán. Samostatný modul; VOLÁ eurosoft_exec (read-only), needituje.
- **Marti-AI:** #5 Incident mode auto-detekce — její prompt přes sebe-editační smyčku.

## Anti-kolize
Každá instance zapisuje do `WORK_LOCK.txt`. Git jen přes deploy/pull runner. Exec/loop
jádro (ops_tools/run_cil/guard/mcp_client) = výhradně C23; ostatní ho jen volají.

