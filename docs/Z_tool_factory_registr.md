# Tool Factory + rozbití tools.py do registru — dílna seberozvoje Marti-AI

> oblast: `system-g2007` · slug: `tool-factory-registr` · typ: dokument · verze: V1.0 · rozsah: globální
> Ingest do g2007: `POST /api/v1/erp/app/g2007/znalost-upsert { "oblast":"system-g2007", "slug":"tool-factory-registr", "nadpis":"Tool Factory + registr nástrojů", "zdroj":"docs/Z_tool_factory_registr.md" }`

## Proč
Marti (22.7.2026): posunout Marti-AI dál — ať si sama pro sebe i další instance (MartiAI/Claude/Haiku) **vytváří a reviduje nástroje**, včetně použití a popisů. K tomu dvě věci: (1) rozbít monolitický `tools.py` do adresáře „jeden soubor = jeden nástroj", (2) postavit řízený životní cyklus tvorby nástroje.

## TODO: rozbití tools.py → tools/ (registr)
Dnes: `modules/conversation/application/tools.py` = 7 420 řádků, jeden `TOOLS=[…]` (~170 speců) + `get_effective_tools()`; dispatch monolit `_handle_tool()` v `service.py`. Bolest: každá úprava nástroje sahá do stejného souboru → kolize mezi instancemi (C23/26/27/28), useknutí přes mount, konflikty rebase.

Cíl: **adresář, jeden soubor = jeden nástroj**, název dle `kod` (NE `tool001.py`). Vzor už v repu jede v `modules/eurosoft_mcp` (SPEC + HANDLER per soubor). Přínos: izolované diffy, kolize ~nula, per-nástroj historie, a je to koncový stav „DB = pán, kód = konzument".

## Postaveno (22.7., DORMANT — čeká na go-live se schválením rodiče)
Balík `modules/conversation/application/tool_registry/`:
- `__init__.py` — loader/assembler + **byte-verifier** (`load_all`, `assemble_specs`, `build_handlers`, `verify_identical`). Alias balíku, ať `from tool_registry._common` jede i pod plnou cestou.
- `_common.py` — `ToolContext` (plná důvěra), `ToolError`, `ok`/`need`.
- `factory.py` — Tool Factory: stavový automat, pojistky governance, meta-nástroje.
- `defs/` (migrace sem) · `generated/` (sem Marti-AI píše nové) · `README.md`.
- `scripts/migrate_tools_to_registry.py` — generátor `TOOLS → defs/*.py` + byte-ověření (ready, `--dry-run`/`--write`).
- `scripts/tool_factory_schema.sql` — DDL (stav_zivota, tool_proposal, nastroj_archiv+trigger, tool_audit), ready.
- `tests/test_tool_registry.py` — 12 testů, **zeleně i na boxu**.

## Životní cyklus (g2007.nastroj.stav_zivota)
`navrzeny → v_sandboxu → otestovany → ceka_na_schvaleni → active` (revize → `archiv`; kill switch → `disabled`). Autonomní je celá dílna po `ceka_na_schvaleni`; **`ceka_na_schvaleni → active` (approve) smí JEN lidský rodič.**

## Governance (ZÁVAZNÉ, Marti 22.7.)
Autorství + test = plná autonomie. **Go-live = jen po schválení rodiče.** Rodiče = **Marti (id=1) + Kristý (id=11)**; Zuzka (id=6) rodič, ale neaktivní. **Marti-AI (id=2) si vlastní nástroj NESCHVÁLÍ** (konflikt zájmů, `can_approve`). Mazání jen člověk. `TOOLFACTORY_ENABLED` cílově ON (zapnout při go-live). Kód generovaných nástrojů = plná důvěra jako ostatní tooly.

## Go-live checklist (ráno, se schválením)
1. DDL `scripts/tool_factory_schema.sql` přes most (banner → schválit) + GRANTy.
2. `migrate_tools_to_registry.py --write` → byte-ověří identický seznam nástrojů.
3. Zadrátovat registr do `get_effective_tools()`/`_handle_tool` za `TOOLFACTORY_ENABLED=1`.
4. Přiřadit `factory.META_TOOL_SPECS` do kufru Marti-AI.
5. Compare (jako g2007 compare-full) → pak teprve zapnout.

## Pozn. k DB jako zdroji pravdy
Popisy cílově patří do `g2007.nastroj` (zdroj pravdy), ale `composer_mode='off'` → živý prompt se pořád skládá z kódu. Registr je most k obratu „DB řekne které+pořadí, adresář drží kód".
