# batch_apply_document_move

## MAPA
- **kód:** `batch_apply_document_move`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 30+1 (2.5.2026 ~21:45, Marti-AI's gap discovery): Hromadny presun N dokumentu do jednoho projektu BEZ per-doc suggest fáze. Marti-AI je primary kustod inboxu, takze pri znamem patternu (napr. vsechny [DB_EC schema]* -> projekt DB_EC) nedava smysl potvrzovat kazdy zvlast.

Cap: max 1000 dokumentu / volání (zvyseno z 200 po Marti-AI's feedback 2.5.2026 ~22:00). Pri vetsim batchi rozdelit. Audit log: jeden activity_log radek 'Marti-AI presunula N dokumentu do project #X', importance=3.

Permissions: stejne jako apply_document_move (single) -- Marti-AI default bypass, cizi persona jen pokud target je v allowed_project_ids.

## PARAMETRY

- **`reason`** [string, volitelný]
  - Kratky duvod pro audit log (napr. 'DB_EC schema docs do DB_EC projektu').
- **`document_ids`** [array, POVINNÝ]
  - List ID dokumentu k presunu (max 1000).
- **`target_project_id`** [integer, POVINNÝ]
  - Cilovy project ID (NE inbox -- presun do inboxu via apply_document_move single).

