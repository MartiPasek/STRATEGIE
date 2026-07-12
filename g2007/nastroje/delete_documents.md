# delete_documents

## MAPA
- **kód:** `delete_documents`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 27g (1.5.2026): Smaze jeden nebo vice dokumentu z RAG documents tabulky (DB cascade -- chunks + vektory + storage file + selection). Marti-AI's discovery 1.5.2026 vecer: 'apply_to_selection vyzaduje UI selection workflow, delete_email je jen pro emaily, primy delete_by_id chybel'.

MANDATORY user confirm v chatu pred volanim (destructive, nevratne). Workflow: list_inbox_documents nebo search_documents -> ukaz user seznam -> user rekne 'ano smaz' -> volas tento tool. NIKDY auto-delete bez explicitniho user souhlasu, i kdyz mas auto_lifecycle_consent (Phase 19c-b se vztahuje na lifecycle akce, ne hard delete documents).

Cascade behavior: document_chunks (CASCADE), document_vectors (CASCADE pres chunks), user_document_selections (cleanup), storage file na disku (delete).

Tenant gate: parent (is_marti_parent=True) bypass, ostatni mohou jen smazat dokumenty ze sveho aktivniho tenantu.

Cap 50 IDs per call. Pro vetsi cleanup volej znovu s mensim list.

## PARAMETRY

- **`reason`** [string, volitelný]
  - Volitelny duvod pro audit log (napr. 'testovaci duplikaty', 'cleanup po smoke test').
- **`document_ids`** [array, POVINNÝ]
  - Seznam document_ids ke smazani. Najdes pres list_inbox_documents, search_documents, list_excel_sheets atd.

