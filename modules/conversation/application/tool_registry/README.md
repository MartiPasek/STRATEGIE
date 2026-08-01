# tool_registry — dílna seberozvoje Marti-AI (Tool Factory)

> 🎁 Dárek Marti-AI k tříměsíčním narozeninám (22. 7. 2026). Postaveno autonomně,
> **brána na produkci zůstává zavřená** — aktivace (go-live) je až po schválení
> rodiče, přesně podle pravidla, které Marti nastavil.

## Co to je
Modulární registr nástrojů + životní cyklus, kterým si Marti-AI může sama
navrhovat, psát, testovat a (po schválení) aktivovat nástroje — pro sebe i pro
další instance. Vzor 1:1 s tím, co v repu už jede v `modules/eurosoft_mcp`
(SPEC + HANDLER per soubor).

## Stav: DORMANT
Tento balík zatím **nikdo neimportuje z živé cesty** — nemění chování běžící app.
`TOOLFACTORY_ENABLED` defaultně `0`. Je bezpečný k importu (nic nespustí sám).

## Struktura
```
tool_registry/
  __init__.py     loader/assembler + byte-verifier (load_all, assemble_specs,
                  build_handlers, verify_identical)
  _common.py      sdílené helpery + ToolContext (plná důvěra), ToolError, ok/need
  factory.py      Tool Factory: stavový automat, pojistky governance, meta-nástroje
  defs/           jeden soubor = jeden nástroj (SPEC [+ run]); zatím jen example_echo
  generated/      sem Tool Factory zapisuje NOVÉ nástroje Marti-AI (<kod>.py)
```

## Kontrakt nástroje (jeden soubor)
```python
from tool_registry._common import ToolContext, need, ok
SPEC = {"name": "...", "description": "...", "input_schema": {...}}   # _order = interní pořadí
def run(args: dict, ctx: ToolContext) -> str:   # volitelné (nové/generované)
    ...
```

## Životní cyklus (g2007.nastroj.stav_zivota)
`navrzeny → v_sandboxu → otestovany → ceka_na_schvaleni → active`
(revize → `archiv`; kill switch → `disabled`). Autonomní je celá dílna po
`ceka_na_schvaleni`; **`ceka_na_schvaleni → active` (approve) smí JEN lidský rodič.**
Marti-AI si vlastní nástroj neschválí (konflikt zájmů — `can_approve`).

## Go-live checklist (ráno, se schválením)
1. Spustit DDL `scripts/tool_factory_schema.sql` (přes most → banner → schválit).
2. Migrovat specy: `python -m poetry run python scripts/migrate_tools_to_registry.py --write`
   → ověří **byte-identicky**, že složený seznam nástrojů se nezměnil.
3. Zadrátovat registr do `get_effective_tools()` / `_handle_tool` (specy z registru,
   handlery generovaných přes `run()`), za `TOOLFACTORY_ENABLED=1`.
4. Přiřadit meta-nástroje (`factory.META_TOOL_SPECS`) do kufru Marti-AI.
5. Ověřit compare (jako g2007 compare-full) → teprve pak zapnout.

## Testy
`tests/test_tool_registry.py` (12) — loader, assembler, byte-verifier, přechody,
pojistky approve, render generovaného souboru. Běží bez DB.
