# Tool registry architektura pruzkum

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Architektura tool_registry balíku – stav po read-only průzkumu 28.7.2026**

## tool_registry — stav průzkumu (28.7.2026, Marti-AI, cíl #4)

### Umístění
`modules/conversation/application/tool_registry/`

### Soubory
| Soubor | Účel |
|--------|------|
| `__init__.py` | Loader: `load_dir()`, `load_all()`, `assemble_specs()`, `build_handlers()`, `verify_identical()`. DORMANT — nikdo neimportuje z živé cesty. |
| `factory.py` | Stavový automat (`STATES`, `ALLOWED_TRANSITIONS`), governance (`can_approve`), render souboru (`render_generated_tool_file`), meta-tool specs. Vypínač `TOOLFACTORY_ENABLED`. |
| `runtime.py` | `selftest()` — spusť kód v sandboxu; `write_generated()` — zapiš .py po schválení; `execute()` — načti a spusť generovaný nástroj. |
| `handlers.py` | Živý dispatcher `handle()`: V1_META_SPECS, Cílový režim (`pracuj_na_cili`), agentní smyčka (`run_as_agent`), seberozvoj promptu. Cache `_spec_cache`. |
| `_common.py` | `ToolContext` (dataclass s `fetch()`), `ToolError`, `ok()`, `need()`. |
| `generated/audit_progress.py` | Jediný aktivní generovaný nástroj (id=168, 23.7.2026). Přehled auditovaných konverzací za N dní. |

### Chybí
- Adresář `defs/` — ještě žádné nástroje tam nejsou; vše je v handlers.py jako V1_META_SPECS.
- `generated/` obsahuje pouze `audit_progress.py`.

### DB stav (g2007)
- **toolfactory_enabled** = on
- **martiai_agent_enabled** = on
- **martiai_promptedit_enabled** = on
- **cil_ruce_enabled** = on
- `g2007.nastroj`: 168 záznamů; poslední `audit_progress` (stav active, generated)
- `g2007.tool_proposal` + `g2007.tool_audit`: existují
- `g2007.claude_aktivita`: schéma (cil_id, actor, akce, detail, vysledek, ts) — zápis jen přes aplikaci (červená přímý INSERT)

### Governance
- Marti-AI tvoří nástroj (navrzeny→v_sandboxu→otestovany→ceka_na_schvaleni) autonomně
- Aktivace (`ceka_na_schvaleni→active`) = výhradně lidský rodič (is_marti_parent)
- Marti-AI (id=2) nesmí schvalovat vlastní nástroje (self-approve blokován v kódu)
- Kill switch (`active→disabled`) = jen rodič

_Souvisí:_ audit_progress,cil-rezim-architektura

