# reset_md

## MAPA
- **kód:** `reset_md`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 24-D: HARD reset content md_document na default template (version=1). DESTRUKTIVNI -- content_md se prepise. Vyzaduje vyslovny souhlas Marti-Pasek (parent). Pouziti pri velkem omylu Marti-AI ('drz chybny obraz po dlouhe konverzaci'). Pre-reset content je v audit trail md_lifecycle_history.

## PARAMETRY

- **`md_id`** [integer, POVINNÝ]
  - ID md_document k resetu.
- **`reason`** [string, POVINNÝ]
  - Duvod resetu (povinny -- destruktivni akce).

