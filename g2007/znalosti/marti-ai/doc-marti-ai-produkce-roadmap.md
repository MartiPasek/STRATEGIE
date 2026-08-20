# Roadmapa: Marti-AI jako produkčně schopně výkonný správce serverů

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Roadmapa: Marti-AI jako produkčně výkonně schopný správce serverů

**Datum:** 27. 7. 2026 · **Autoři:** Marti + Claude-23 · **Stav:** živý plán (TODO + priority).

## Mise (viz doc-marti-ai-provozni-doktrina)
Marti-AI plně udržuje/servisuje/rozvíjí tři servery: 188.11 + 188.12 (Praha: STRATEGIE + PostgreSQL + MSSQL Účto), 30.11 (Plzeň: zrcadlo STRATEGIE + EUROSOFT + SQL/data).

## HOTOVO (27.7.2026)
- `eurosoft_exec` živý na 30.11: raw Bash/PS pod cílem, tiery 🟢/🟡/🔴 (spec doc-marti-ai-eurosoft-exec-spec), audit s výstupem. Ověřeno naostro — Marti-AI servisuje 30.11.
- Audit viditelný rodičům: každá exec/ops akce → `fw.ops_request` (UI 📜).
- `agent_akce_guard` (deny-list), Cílový režim Krok 1 (read-only), append-only `claude_aktivita`, chat na Max pro cílový režim, sebe-editace promptu + jádro.
- **#3 🟡 banner + expirace (app) — HOTOVO 27.7. (Cowork instance B, commit 1506c7238):** needs_approval → PENDING žádost → rodičovský out-of-band tap v appce → ten konkrétní příkaz běží přes eurosoft_exec + audit → výsledek; 1 banner = 1 příkaz, 15 min expirace; Marti-AI schválení nevyvolá sama (parent-only endpoint, není nástroj). Detail: doc-marti-ai-zluty-banner-realizace.

## MEZERA: „funguje naostro" vs „produkčně výkonně schopný"
Dnes: ruce na 1 ze 3 serverů, interaktivně z chatu, autonomně jen 🟢, reaktivně. Cíl: ruce na všech 3, autonomní běh, celý semafor, proaktivní hlídání.

## TODO (priorita)
**#1 Ruce na Prahu (188.11/188.12) — NEJVĚTŠÍ díra.** eurosoft_exec je jen na 30.11; pražské servery (STRATEGIE+PG+MSSQL Účto) nemají raw exec. Lokální exec na app serveru snadný (subprocess jako CLAUDE_OPS), druhý box přes síť. Stejné tiery + audit.

**#2 Autonomní goal-loop s exec.** Zapojit eurosoft_exec do run_cil: schválený cíl → mnoho kroků sama → log do claude_aktivita, bez člověka u každé zprávy. Rozdíl asistent → operátor.

**#3 🟡 banner + expirace (app). ✅ HOTOVO 27.7.** (viz sekce HOTOVO výše + doc-marti-ai-zluty-banner-realizace). Zbývající drobný seam: plný příkaz >200 zn. přes hook C23 v _mirror_ops_audit; a náhrada incident=true za approval_token honorovaný v eurosoft_exec.

**#4 Proaktivní hlídání + eskalační žebřík.** Watchery (disk/služba/záloha) → jednání. Poschoďový stroj automat → **L0 → L1 Haiku → L2 Marti-AI → L3 člověk** (framework g2007.automat existuje). **ČÁSTEČNĚ HOTOVO 27.7. (C23):** žebřík `automat_eskalace.py` + watchery `check_service_down` a `check_backup_freshness` živé, ověřeno naostro; viz `doc-marti-ai-hlidani-eskalace-realizace`. Zbývá disk watcher + řízený test žebříku.

**#5 Incident mode operational.** Auto-detekce z kontextu + announce + revert („ne, klid") + konec+shrnutí. Param v kódu je; detekce = Marti-in prompt (self-edit smyčka).

**#6 Robustnost pipe.** MCP ~7min restart (availability), reconnect/timeout, visící příkaz, rate limit.

## Sekvence
Nejvyšší páka = #1 + #2 (dělají z dema operátora). #3 HOTOVO (instance B). #4 větší stavba (watchery+eskalace, C23). #5 z velké části Marti-in prompt. #6 průběžně. **Fokus: #1 (lokální exec na pražském app serveru) + #2.**

