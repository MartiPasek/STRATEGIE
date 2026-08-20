# Roadmapa Marti-AI autonomní operátor — stav 29. 7. 2026 (živý plán)

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Roadmapa „Marti-AI autonomní operátor" — stav 29. 7. 2026

Živý plán, aktualizace k doc-marti-ai-produkce-roadmap-stav-28-07. Autor: Claude-23. Směr (Marti): Marti-AI staví a opravuje sama sebe (prompt i kód), C23 jistí; malý prompt + naloz si kufr per činnost; agent mód výchozí.

## HOTOVO (odškrtnuto)
- **#1 Ruce** — pražské (strategie_exec) + plzeňské (eurosoft_exec), tiery 🟢🟡🔴 + audit. 2 izolované ruce (cross-server bez VPN nejde).
- **#2 Autonomní goal-loop s rukama** — nasazen A OVĚŘEN naostro (cíl #5). Py3.14 double-wrap CallToolResult vyřešen.
- **#3 Žlutý banner + expirace** — hotovo.
- **#4 Watchery + eskalace** — z velké části (automat_eskalace L0→L3, check_service_down, check_backup_freshness).
- **Self-code-edit smyčka** (navrhni_zmenu_kodu → schval rodič) + audit deployů do fw.ops_request.
- **NOVÉ 29.7.: Patch mód pro velké soubory** — navrhni_zmenu_kodu_patch (kotvy old→new, unikátní) + drift guard. Marti umí editovat i service.py/tools.py bez posílání celého obsahu.
- **NOVÉ 29.7.: Kufr mechanismus nasazen** — pack-aware lean default v service.py (návrh #3, commit f581a133a). Zatím INERTNÍ (flag off).
- Oprava strategie_file_read/list project_root (auto-detekce ze __file__).
- Governance uklizena (rodiče Marti/Kristý; admini +Jirka; Zuzka „teta"; trust_rating vs is_marti_parent oddělené).
- API health watchdog (per-instance A/B, auto-restart + alert adminům) — doplňuje #4.

## ZBÝVÁ (prioritně)

### 1. Kufr — dokončit aktivaci (HNED, večer 29.7.)
Mechanismus nasazen, inertní. Zapnout `lean_default_enabled='on'`, **změřit vstupní tokeny před/po** na jedné konverzaci (~167→~40 nástrojů = ~68% páka), ověřit `load_pack` per činnost s lean ON, pak udělat standardem. = „malý prompt + naloz si kufr" + předpoklad bodu 2.

### 2. Agent mód jako výchozí (velký směr)
- Rozšířit governed sadu + **napojit 🟡 banner-cestu** (agent citlivější akci NAVRHNE ke schválení, ne jen odloží).
- Přidat ruce i do `run_goal` (freeform cíle bez g2007.cil).
- Cílově: agentní engine výchozí i pro konverzaci (chat composer = doplněk).

### 3. Spolehlivost agentní smyčky (TICHÝ BLOKÁTOR — pozorováno 29.7.)
Marti opakovaně odpoví v chatu („jdu na to"), ale sama nevejde do `pracuj_na_cili` — nutné doťukávat. Pro skutečnou autonomii: spolehlivý přechod potvrzení→akce (wake rovnou do agentní smyčky / úprava promptu/logiky). Bez tohohle je to „poloautonomní s ťukáním".

### 4. Watchery + incident (zbytek #4–#6)
`check_disk` watcher (chybí); `smoke_eskalace` naostro (L0→L3); 2 watchery ve stavu chyba (`check_legacy_errors`, `check_vp_freshness`) — prověřit; **#5 Incident mode** (auto-detekce incidentu do promptu Marti-AI = její sebe-editace); **#6 robustnost pipe** (MCP restart/reconnect/timeout/rate-limit).

### 5. Drobnost
`pracuj_na_cili` hláška pořád píše „read-only", i když ruce má — sjednotit.

## Nejkratší cesta k „jede to samo"
Bod 1 (kufr) → bod 3 (spolehlivost smyčky) → bod 2 (agent default). Bod 3 nejvíc rozhoduje mezi „autonomní" a „poloautonomní s ťukáním".

