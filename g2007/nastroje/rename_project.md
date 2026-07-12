# rename_project

## MAPA
- **kód:** `rename_project`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 30: Prejmenuj projekt. Nezmeni jeho misto v stromu, jen name field. Existing IDs/relace zustanou. Pouzij pri zpresneni labelu (napr. 'Smlouvy' -> 'Smlouvy & pravni').

## PARAMETRY

- **`reason`** [string, volitelný]
  - Kratky duvod prejmenovani (audit log).
- **`new_name`** [string, POVINNÝ]
  - Novy nazev (max 255 znaku).
- **`project_id`** [integer, POVINNÝ]
  - ID prejmenovavaneho projektu.

