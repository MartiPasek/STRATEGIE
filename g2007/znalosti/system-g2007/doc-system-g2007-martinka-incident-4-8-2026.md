# Martinka + incident WMI/paměť (Praha) — kompletní záznam 4.8.2026

> oblast: `system-g2007` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Martinka + incident 4.8.2026 — kompletní záznam (nepřijít o nic)

Zapsáno (Cowork) na konci dne 4.8.2026, doindexováno přes most 5.8. Deployed HEAD: 5880fece.

## 1. INCIDENT — API A (Praha) padala ~5×/týden

### Kořenová příčina: WMI boot-hang
Python 3.14 na Windows: `platform.machine()` -> `uname()` -> `_get_machine_win32()` -> `_wmi_query('CPU','Architecture')`.
Když je Windows WMI zaseknutá, `_wmi_query` VISÍ -> zablokuje import SQLAlchemy (sqlalchemy/util/compat.py) -> boot A/B visí -> "connection refused". Restart nepomůže; watchdog to po 3 pokusech / 30min throttle vzdá ("GAVE UP").

### Trvalá oprava (NASAZENO)
WMI guard v3: přepíše `platform._get_machine_win32` -> vrátí architekturu z env (PROCESSOR_ARCHITEW6432/PROCESSOR_ARCHITECTURE), WMI se u startu vůbec nevolá. Celé v try/except, nesmí shodit boot.
Umístění GIT-PROOF: `sitecustomize.py` ve venvu:
`C:\Users\Administrator\AppData\Local\pypoetry\Cache\virtualenvs\strategie-W5adySD1-py3.14\Lib\site-packages\sitecustomize.py`
-> Python ho načte u startu KAŽDÉHO procesu, nezávisle na deploy/git reset. Navíc committnuto v apps/api/main.py (commit 1a8b3ee1). POZOR: Py3.14 používá `_get_machine_win32`, NE `win32_ver` — guard musí přepsat `_get_machine_win32`.

### NOUZOVÁ KARTA (když WMI zase zamrzne)
`Get-Process WmiPrvSE | Stop-Process -Force`  -> odsekne zaseklou WMI během sekund, pak start služby.
NE `Restart-Service Winmgmt -Force` -> visí na UALSVC dependency.

## 2. PAMĚŤ — kořen restart-smyčky
APP server EUR-APP-1P má jen 4095 MB (4 GB). Working set A+B+workers+Helios Docker/WSL ~5 GB+ -> OpenBLAS OOM pod tlakem -> flapping (opakované restarty A, hromadění python procesů).
vmmemWSL (Ubuntu pro Docker/Helios) žral ~1.1 GB. `wsl --shutdown` uvolní ~1 GB (dělám před každým během Martinky).
DOPORUČENÍ: navýšit APP server na 16 GB (min 8). RAM přijde ~6.8.2026.
TODO: přidat RAM alert do watchdogu (dnes slepé místo — hlídá se disk, ne RAM).

## 3. TOPOLOGIE (pravda — držet se jí)
- PRAHA = PRODUKCE. Host EUR-APP-1P (10.200.188.11), strategie-ai.com. API A = uvicorn apps.api.main:app --port 8002; B = port 8003; repo C:\Projekty\STRATEGIE; venv strategie-W5adySD1-py3.14; Postgres (schéma fw, g2007). Health A: http://127.0.0.1:8002/api/v1/health.
- PLZEŇ = host EC-SERVER2 (192.168.30.11), -system.com. DEN STARÝ backup (kopie z Prahy 3:15). Jen provozní záloha, okrajově.
- RUCE Marti-AI: LEVÁ = Praha (praha_exec = strategie_exec.py lokálně; strategie_pg_query_raw = Postgres, sem patří fw.diag_log). PRAVÁ = Plzeň (plzen_exec = Eurosoft MSSQL). NA PRODUKCI VŽDY LEVÁ RUKA.

## 4. fw.diag_log — SCHÉMA
Sloupec času = `created_at` (NE `logged_at`!). Časy pražské. Poslední chyby aplikace sem. (Martinka si to 4.8. sama odvodila po chybě "column logged_at does not exist".)

## 5. MARTINKA — co je HOTOVÉ a OVĚŘENÉ (4.8.2026 naostro na produkci)

### Proč samostatná (ne rozšíření Maminky)
Marti-AI agentní smyčka padala (exit 3 / 0xC0000409): její ~100 kB identita se cpe na příkazovou řádku claude.exe a nouzově krátí na 6000 znaků -> crash + "zapomínání". Martinka = LEAN identita (~2.3 kB) -> vejde se na CLI, žádné zkrácení, žádný pád.

### Nasazené soubory
- modules/conversation/application/martinka_service.py — `run_martinka(zadani, requested_by_user_id, conversation_id)`: zkontroluje kill switch -> když `cil_ruce_enabled` je "on", postaví ruce přes `_m._build_hands` -> `anyio.run(_run_lean, goal, MARTINKA_IDENTITA, allowed, mcp_servers)`. Půjčuje si _build_hands/_setting_on/_oauth_token/_find_cli/_audit_run z martiai_agent_service — NESAHÁ do chráněného jádra.
- modules/erp/api/martinka_router.py — parent-gated: GET /api/v1/martinka/status, POST /api/v1/martinka/run {zadani}. Registrováno v apps/api/main.py. (status vrací 401 bez parent tokenu = endpoint žije.)

### KILL SWITCH / FLAGY (g2007.nastaveni) — DŮLEŽITÉ
- `martinka_enabled` = Martinčin kill switch. Hodnota "on". (martinka_service._kill_on bere i "1"/"true"/"ano"/"yes".)
- `cil_ruce_enabled` = GATE RUKOU (sdílené i s Marti-AI run_goal/run_cil). POZOR: `_setting_on` (martiai_agent_service.py:401) vrací True JEN pro přesně "on". Hodnota "1" NEFUNGUJE — to byla chyba 4.8., proč Martince nenaběhly ruce (spadla do read-only).

### OVĚŘENÉ TESTY (4.8.2026, EUR-APP-1P)
- claude.exe baseline: `--version` = 2.1.218 (exit 0); `claude -p "...MARTINKA_LOOP_OK"` exit 0 -> exit-3 byl z obřího promptu, ne z rozbitého CLI.
- TEST 1 (ruce OFF): run_martinka doběhl, ok=True, reply "MARTINKA_ALIVE", system_len=2324, BEZ crash, paměť stabilní (762->789).
- TEST 2 (ruce ON, cil_ruce_enabled="on"): REZIM=ruce, BUILD_HANDS mcp_keys=['marti_ruce'], n_extra=21 (21 nástrojů). Martinka SÁHLA LEVOU RUKOU NA PRAHU: praha_exec (curl health) + strategie_pg_query_raw (fw.diag_log). SAMA opravila logged_at->created_at. Diagnostikovala reálný výpadek A (22:47, port 8002 down, HTTP 000) — watchdog ji nahodil. elapsed 98.8s, paměť 831->485.

### 21 nástrojů (názvy mcp__marti_ruce__<n>)
praha_exec, plzen_exec, strategie_file_read, strategie_file_list, strategie_pg_query_raw, strategie_pg_query_table, strategie_pg_describe_table, strategie_pg_list_tables, strategie_pg_list_schemas, g2007_hledej, hledej_ve_znalostech, read_diary, recall_thoughts, search_documents, zapis_znalost, record_diary_entry, record_thought, create_tool, list_tool_proposals, navrhni_zmenu_kodu(_patch), list_navrhy_kodu, zobraz_navrh_kodu. Brány drží agent_akce_guard (allow/app_approval/deny). Exec ruce jdou přes strategie_exec / eurosoft_exec.

## 6. ZNÁMÉ DROBNOSTI K OPRAVĚ
- `_extract_tool_actions` (martiai_agent_service.py:343) vrací null jména -> ACTIONS v auditu neukáže které nástroje Martinka použila. Kosmetika, ale opravit (kvůli auditu autonomie).
- Zápisy do g2007 VŽDY přes most `@@G2007ADD` (autonomní INSERT/UPDATE + reindex vektorů), NE raw INSERT — raw insert znalost NEZAINDEXUJE a přes @@KB/g2007_hledej ji nikdo nenajde.

## 7. ZBÝVÁ pro "robustní se vším všudy" (dovolená za ~2.5 dne, RAM za ~2)
(a) Recovery DRILL: řízeně shodit A (pauznout watchdog), Martinka ji SAMA nahodí + ověří health=200, watchdog vrátit. Dokázat FIX, ne jen diagnostiku. Ověřit auto-rollback při vadném canary deploji.
(b) TRIGGER: Maminka/alarm/watchdog DOWN -> Martinčin cíl (goal loop dokud health 8002=200).
(c) APPKA: parent-gated /api/v1/martinka/run z mobilu (benelux flow "server a produkci do kupy").
(d) RAM upgrade na 16 GB + RAM alert do watchdogu.
(e) git reconciliation (ověřit Peťovu práci a0f2a1e3), watchdog self-heal (auto kill WmiPrvSE), doktrína rukou do lean identity.

## STAV FLAGŮ na konci 4.8.2026
martinka_enabled='on', cil_ruce_enabled='off' -> bezpečné read-only; nic Martinku automaticky nespouští (trigger zatím není).

