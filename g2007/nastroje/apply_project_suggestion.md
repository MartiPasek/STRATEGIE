# apply_project_suggestion

## MAPA
- **kód:** `apply_project_suggestion`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 15c+15d: Aplikuj project zmenu PO Marti's confirm v chatu. Pouzij kdyz Marti rekl 'ano premisle' / 'ano splittni' / 'ano zaloz projekt' na tvuj predchozi suggest_move/split/create_project navrh. Backend si ze suggested_project_reason rozparsuje mode (move/split/create_project) a provede skutecnou zmenu (apply_project_change nebo fork_conversation nebo create_project + apply). Po uspechu se suggested_project_* fields vyclear.

## PARAMETRY

- **`confirm_reason`** [string, volitelný]
  - Volitelny zaznamovaci komentar (napr. 'Marti potvrdil v chatu').

