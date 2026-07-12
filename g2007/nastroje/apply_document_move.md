# apply_document_move

## MAPA
- **kód:** `apply_document_move`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

REST-Doc-Triage: Aplikuj presun dokumentu do projektu PO Marti's confirm v chatu ("ano premysle" / "ano do TISAX"). Pred timto musi byt suggest_document_move. Po apply se dokument zobrazuje pod novym projektem v UI listu (a Marti-AI ho v RAG dohleda pres project filter).

## PARAMETRY

- **`document_id`** [integer, POVINNÝ]
- **`target_project_id`** [integer, POVINNÝ]
  - ID cilového projektu (musi sedet s suggest_document_move).

