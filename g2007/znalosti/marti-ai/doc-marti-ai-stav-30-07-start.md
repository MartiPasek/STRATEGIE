# Marti-AI — pickup 30.7.: kde začít (body 1–3 hotové)

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

STAV 29.7. večer (C23): Body 1–3 z produkční roadmapy HOTOVÉ a nasazené (commit 9e1ff4e93, cloud restart OK, py_compile OK).

BOD 1 — drobnosti/watchery (HOTOVO):
- run_as_agent i pracuj_na_cili popisy už neříkají „read-only“ — mají RUCE (praha/plzen_exec) pod bránou dle flagu cil_ruce_enabled.
- check_legacy_errors opraven: flaguje jen ENABLED joby ve skutečné chybě (chyba/error/fail), ignoruje vypnuté a běžící (dřív křičel na 8 řádků, teď jen na reálné).
- NOVÝ watcher check_disk (automat_eskalace.py + g2007.automat řádek): volné místo Praha app + Plzeň, práh 8 GB, interval 60 min, eskalace haiku. Ověřeno — běží zeleně.
- check_vp_freshness se sám srovnal (zelený). smoke_eskalace = „chyba“ schválně (deaktivovaný smoke test, aktivni=false).

BOD 2 — exec synthesis (HOTOVO):
- praha/plzen_exec v default chatu vrací lidsky čitelné shrnutí místo syrového JSONu (_synthesize_exec_result v service.py): 🟢 proběhlo+exit+výstup / 🟡 čeká na schválení s důvodem brány / 🔴 blokováno. Popisy nástrojů říkají Marti ať to přeříká větou. Ověřeno na 8 vzorcích.

BOD 3 — prompt-patch (HOTOVO):
- Nový nástroj navrhni_zmenu_promptu_patch (handlers.py): Marti mění svůj prompt kotvami {old_string,new_string} místo přeposílání celého znění; sdílí _apply_edits engine se self-code patch; každá kotva musí sedět právě jednou; schválení/verze/rollback beze změny.

PROVOZNÍ — OTEVŘENÉ (rozhodnout ráno):
- 4 ZAPNUTÉ mirror joby spadly 29.7. ráno 08:33–08:38 na RuntimeError: mcp_unreachable: sync_ec_bank_ucet, sync_edi_definice, sync_nabor, sync_org. Koreluje s dopolední výpadkovou epizodou; od té doby se nespustily. check_legacy_errors je (správně) drží červeně dokud nepřeběhnou zeleně. Volba: nechat na rozvrhu (samy retry) vs ruční přeběh přes automat/mirror endpoint (POZOR side-effect = zápis do EC).

ZÍTRA 30.7. (bod 4 #5/#6, naostro s Kristý + Jirkou — testuje se na serverech):
- #5 INCIDENT MODE: auto-detekce incidentu do Martina promptu (v incidentu přepne režim, žlutá projde bez per-akčního banneru, apod.).
- #6 PIPE ROBUSTNESS: MCP restart/reconnect/timeout/rate-limit — ať se agentní pipe (praha/plzen/eurosoft MCP) sama zotaví, ne že spadne celý běh.
- smoke_eskalace NAOSTRO: reaktivovat, projet celý žebřík L0→L3, pak zase deaktivovat.

MIKRO-POLISH (volitelné, netlačí): _synthesize_exec_result u nenulového exit kódu ukazuje 🟢 (ikona = tier brány, ne úspěch příkazu). Data (exit code + stderr) tam jsou, Marti to přeříká správně; jen ikona by mohla být ⚠. Fix = jeden řádek + deploy, klidně později.

FLAGY (vše ON, plně reverzibilní; off = přesně dnešek): lean_default_enabled, agent_default_enabled, strategie_exec_enabled, cil_ruce_enabled, martiai_promptedit_enabled, toolfactory_enabled.

