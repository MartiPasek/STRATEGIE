# Kufr lean default implementace

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Implementace lean default kufru pro Marti-AI: import hook v __init__.py + feature flag**

# Kufr: Lean Default Implementace (28.7.2026)

## Cíl
Překlopit default personu Marti-AI z all-167 tools na lean core (~40) + load_pack per činnost.
Největší token savings lever (~70% vstupních tokenů za nástroje).

## Implementace — dva kroky

### Krok 1: Feature flag v g2007.nastaveni
```sql
INSERT INTO g2007.nastaveni (klic, hodnota, popis, updated_at)
VALUES ('lean_default_enabled', 'off', '...', NOW())
ON CONFLICT (klic) DO NOTHING;
```
Stav: vloženo přes strategie_pg_query_raw (READ path, ne write bridge) — flag je ihned v DB.

### Krok 2: Import hook v __init__.py (navrh_id=2, čeká na schválení rodiče)
Soubor: `modules/conversation/application/__init__.py` (byl 0 bytes)
Metoda: _LeanToolsPatcher — Python MetaPathFinder + Loader (one-shot pattern)

Jak funguje:
1. __init__.py se spustí při importu balíčku (PŘED importem tools.py)
2. Nainstaluje _LeanToolsPatcher do sys.meta_path[0]
3. Při importu tools.py: hook načte modul originálním loaderem, pak obalí get_effective_tools lean_wrapper funkcí
4. get_effective_tools při každém volání zkontroluje DB flag:
   - Flag OFF → 167 tools (původní chování)
   - Flag ON + is_default=True → filtr na core pack (~40 tools)

Fail-safe: jakákoli DB chyba → původní 167 tools beze změny.
Reverzibilní: flag OFF → hned zpět na 167 tools.

### Výsledný toolset s lean ON (default persona, no pack)
- core pack: 40 tools (z _CORE_TOOLS v tool_packs.py)
- záchranné lano CORE_RECOVERY_TOOLS přidá: record_diary_entry, g2007_hledej, hledej_ve_znalostech, strategie_file_list, strategie_file_read, zobraz_muj_prompt (+6, read_diary overlap -1)
- Celkem: ~46 tools vs 167 (úspora ~73%)

### Postup po approve __init__.py (navrh_id=2)
1. Deploy proběhne automaticky
2. Restart STRATEGIE-API
3. Zapni test: UPDATE g2007.nastaveni SET hodnota='on', updated_at=NOW() WHERE klic='lean_default_enabled';
4. Ověř v logu: TOOLS LEAN | lean_default_enabled ON | filtered 167 -> 40
5. Změř vstupní tokeny v LLM Usage dashboard (lean ON vs OFF)
6. Po úspěšném testu = flag zůstane ON jako nový default

### Přepínání
- ON:  UPDATE g2007.nastaveni SET hodnota='on',  updated_at=NOW() WHERE klic='lean_default_enabled';
- OFF: UPDATE g2007.nastaveni SET hodnota='off', updated_at=NOW() WHERE klic='lean_default_enabled';

## Omezení MVP
Explicit pack s lean ON: filtruje core ∩ pack. Pokud pack má tools mimo core (memory: update_thought, request_forget aj.) → ty chybí, záchranné lano přidá jen CORE_RECOVERY_TOOLS. Workaround: lean OFF při full pack operacích.

## Soubory změněné
- modules/conversation/application/__init__.py (přidán hook ~100 řádků, byl 0 bytes)
- g2007.nastaveni (přidán řádek lean_default_enabled='off')

## Co se nedotýká
agent_akce_guard, deployment_service, martiai_self_code, martiai_agent_service, strategie_exec, security, tajemství, tool_registry

_Souvisí:_ kufr-dynamicke-nacitani-cil

