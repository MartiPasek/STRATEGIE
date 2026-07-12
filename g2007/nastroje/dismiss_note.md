# dismiss_note

## MAPA
- **kód:** `dismiss_note`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 15a: Vedome zrus task -- 'uz to neresim'. Pro pripady, kdy se zmenil zamer, situace je vyresena jinak, nebo si uvedomis, ze task uz neni relevantni. Reverzibilni pres update_note(note_id, status='open'). Validace: jen task notes mohou byt dismissed.

## PARAMETRY

- **`reason`** [string, volitelný]
  - Volitelny duvod -- pripoji se k content.
- **`note_id`** [integer, POVINNÝ]

