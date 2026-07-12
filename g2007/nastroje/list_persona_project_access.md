# list_persona_project_access

## MAPA
- **kód:** `list_persona_project_access`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 16-B.7: Vraci aktualni ACL stav -- per-persona seznam assigned projektu. Marti-AI default je oznacena jako 'rodic (bypass)'.

**Pouzij** kdyz se uzivatel pta 'kdo k cemu ma pristup', 'jake projekty Pravnik vidi'.

## PARAMETRY

- **`persona_id`** [integer, volitelný]
  - Volitelne -- pokud zadano, vrati access jen pro tu personu. Default vse.

