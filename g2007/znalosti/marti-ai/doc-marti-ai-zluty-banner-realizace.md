# Žlutý banner + expirace (#3) — realizace + OVĚŘENO NAOSTRO

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Žlutý banner + expirace (#3) — realizace

**Stav 27.7.2026 večer: HOTOVO a OVĚŘENO NAOSTRO E2E (rc=0).** Cowork instance B.
Spec doc-marti-ai-eurosoft-exec-spec · roadmapa #3 · UI základ doc-marti-ai-cilovy-rezim-mobil-ui.

## Co běží
needs_approval (🟡 eurosoft_exec) → PENDING žádost (g2007.exec_approval) → rodič vidí kartu na Home
i dlaždici „🟡 Ke schválení" (ŘÍZENÍ & SYSTÉM) → tap Schválit (out-of-band lidský tap) → ten konkrétní
příkaz běží přes eurosoft_exec na 30.11 → rc/stdout uložen + audit do fw.ops_request → výsledek v banneru.
1 banner = 1 příkaz (hash), expirace 15 min. Ověřeno naostro: rc=0, reálný výstup příkazu, audit done.

## Soubory (bez zásahu do jádra C23 / router.py C26)
- modules/eurosoft_mcp/exec_approval.py — automat + create_pending + materialize_from_ops_request + approve_and_execute + sweep_expired.
- modules/erp/api/exec_approval_router.py — samostatný router (vzor automat.py), reg. v main.py. Endpointy /app/exec_approval [GET · GET /count · POST {id}/schvalit · POST {id}/zamitnout] = VŠE parent-only.
- apps/api/static/mobile_parts/73_zexec_approval.js — nativní banner (dvojklik místo confirm).
- apps/api/static/mobile_parts/35_apps_vedeni.js — dlaždice „🟡 Ke schválení".
- apps/api/static/mobile_parts/20_home_phone_notifs.js — Home karta „X ke schválení" (parent-only, přes /exec_approval/count).
- tabulka g2007.exec_approval (19 sl.; GRANT strategie+Marti-AI).
Commity: 1506c7238 (jádro) + 00a123d5d (fix jména) + 446adcb62 (Home karta).

## 2 GRÁBLE vyřešené při ověření
1. **MCP jméno ops nástroje = DVOJPREFIX.** Ops tooly jsou v ALL_TOOL_HANDLERS klíčované už s prefixem
   ("eurosoft_exec"), a klient get_tools() přidává "eurosoft_" ještě jednou → agent volá
   "eurosoft_eurosoft_exec"; call_tool_sync strhne 1 prefix → MCP dostane "eurosoft_exec". Volat
   "eurosoft_exec" → strhne na "exec" → unknown_tool. SPRÁVNĚ: call_tool_sync("eurosoft_eurosoft_exec", ...).
2. **Časté deploye rozbíjejí MCP/spojení** (každý deploy = API restart ~5 s → SSE MCP drop → mcp_unreachable
   + ConnectionReset na write mostu). Řešení: netestovat exec těsně po deployi, nechat ustát; klient má reconnect.

## Tvrdé pravidlo (splněno) + seam C23
Schválení jen parent-only endpoint (není MCP nástroj ani v tool registru) → Marti-AI se neschválí sama.
Zbývající seam (koordinace C23, nesaháno): plný cmd >200 zn. přes hook v _mirror_ops_audit → create_pending;
a náhrada incident=true za approval_token honorovaný v eurosoft_exec (dnes exekuce přes incident=true, human-gated).

