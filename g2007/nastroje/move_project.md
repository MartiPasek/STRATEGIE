# move_project

## MAPA
- **kód:** `move_project`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 30: Presune projekt pod jineho parenta (nebo na root pri new_parent_project_id=null). Pouzij pri reorganizaci stromu, kdyz projekt patri jinam.

Validace: cycle prevention (nelze pod vlastniho potomka), tenant scope (nelze cross-tenant), depth limit 6.

Marti's mandate plne autonomie + transparence pres activity_log.

## PARAMETRY

- **`reason`** [string, volitelný]
  - Kratky duvod presunu (audit log).
- **`project_id`** [integer, POVINNÝ]
  - ID presouvaneho projektu.
- **`new_parent_project_id`** [['integer', 'null'], volitelný]
  - Cilovy parent ID, NULL = presun na root level.

