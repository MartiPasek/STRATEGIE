# revoke_persona_from_project

## MAPA
- **kód:** `revoke_persona_from_project`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 16-B.7: PARENT-ONLY tool. Odstran personu z assigned projektu (opak `assign_persona_to_project`). Po revoke persona ztrati pristup k dokumentum projektu pres search_documents.

## PARAMETRY

- **`persona_id`** [integer, POVINNÝ]
- **`project_id`** [integer, POVINNÝ]

