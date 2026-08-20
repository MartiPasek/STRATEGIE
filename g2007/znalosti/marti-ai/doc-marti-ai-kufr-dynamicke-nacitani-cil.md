# Kufr — překlopení defaultu na lean core + načítání per činnost (cíl 28.7.)

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Kufr — dynamické načítání nástrojů (cíl)

**Staví Marti-AI sama** přes self-code-edit smyčku. **C23 jistí** (review návrhů, chráněné jádro, schvalování rodičem). Zapsáno 28. 7. 2026.

## Cíl
Překlopit default personu z „vidí všech 167 nástrojů" na **lean core + kufr per činnost**. Nástroje tvoří ~68 % vstupních tokenů (doc `nastroje`) — tohle je největší páka úspory. Malý prompt → Marti-AI si podle cíle naloží jen pár nástrojů, které pro danou činnost potřebuje, a s tím jde do dalšího turnu.

## Současný stav (rekognoskace C23, 28.7.)
- `tools.py get_effective_tools(is_default)`: pro default personu vrací `_base = TOOLS` (**všech 167**); specializovaná role dostane CORE bez MANAGEMENT_TOOL_NAMES.
- `service.py` (~ř. 11319–11344): `effective_tools = get_effective_tools(...)`, pak **subtraktivní** pack filtr — spustí se **jen když `conv.active_pack` není NULL**. Default `active_pack=None` → žádný filtr → všech 167.
- `tool_packs.py`: pack infra existuje. `PACKS` = core (~40 nástrojů, lean base), tech, memory, editor, admin + role packy (pravnik_cz/de, psycholozka). `get_pack`, `list_pack_names`, `is_valid_pack`. Core už obsahuje `load_pack`/`unload_pack`/`list_packs`/`set_pack_overlay`.
- Zdroj pravdy dle designu = tabulka `nastroj` (mapa→popis→parametry); kód dnes jede na Python listech. **Migraci na DB `nastroj` NEřešit v tomto cíli** (to je samostatný, větší kus).

## Rozsah (co v tomto cíli JE)
Překlopit default tak, aby normální turn startoval **lean (core)** a Marti-AI si kufr pro činnost **doložila za běhu** (`load_pack`). Ne big-bang — inkrementálně, měřitelně, reverzibilně.

## Guardraily (POVINNÉ — jistí C23)
1. **Za feature flagem** (g2007.nastaveni, vzor `cil_ruce_enabled`). Default **OFF**, dokud není ověřeno. Flag OFF = přesně dnešek (all-167).
2. **Chráněné jádro se nedotýká**: agent_akce_guard, deployment_service, martiai_self_code, martiai_agent_service, strategie_exec, security, tajemství, tool_registry/handlers. Tvrdá brána to blokuje — ani nenavrhovat.
3. **Inkrementálně**: nejdřív opt-in flag, ověř na jedné konverzaci, **změř vstupní tokeny před/po**, teprve pak zvažovat globální default.
4. **Bezpečnostní síť**: když LLM potřebuje nástroj mimo core, musí ho umět doložit (`load_pack`). Ověř, že packy pokrývají běžné potřeby včetně **rodičovského dohledu, self-code smyčky a paměti** (load_pack/list_packs/navrhni_zmenu_kodu/record_thought…). Marti-AI se nikdy nesmí „zamknout" bez cesty ven.
5. **Každá změna kódu jde přes `navrhni_zmenu_kodu` → `schval` rodič.** Žádný přímý zápis do repa.
6. **Reverzibilní**: jeden přepínač zpět na dnešek.

## Akceptační kritéria
- [ ] Feature flag existuje, default OFF; se zapnutým flagem default turn startuje s **core (~40)** místo 167.
- [ ] Marti-AI si v běhu naloží správný pack pro daný cíl — **prokázáno na reálném cíli** (ne teoreticky).
- [ ] **Naměřená úspora vstupních tokenů** (před/po) doložena číslem.
- [ ] Rodičovský dohled + self-code + paměť zůstávají dostupné (přes core nebo load_pack).
- [ ] Flag OFF = beze změny chování (regrese ověřena).

## Kroky (návrh, Marti-AI si upraví)
1. Založ feature flag v g2007.nastaveni (např. `lean_default_enabled`), default OFF; přečti ho v service.py před pack filtrem.
2. Uprav logiku: když flag ON a `active_pack` je NULL a je to default persona → chovej se jako `active_pack='core'` (filtr na core). Přes `navrhni_zmenu_kodu`.
3. Ověř pokrytí core: obsahuje self-code/paměť/load_pack/dohled? Kde ne, doplň do core nebo zajisti snadné `load_pack`.
4. Zapni flag na jedné testovací konverzaci, změř tokeny před/po, dolož.
5. Napiš zpět C23 (přes most) výsledek + číslo úspory; C23 jistí a rozhodne o globálním překlopení.

