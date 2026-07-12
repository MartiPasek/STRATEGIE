# assign_persona_to_project

## MAPA
- **kód:** `assign_persona_to_project`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 16-B.7: PARENT-ONLY tool. Pridej cizi persone (Pravnik, Honza, atd.) pristup ke konkretnimu projektu. Marti-AI default pristup nepotrebuje (je rodic, vidi vse). Inbox NIKDY -- zustava Marti-AI kustod role.

**Pouziti**: Marti rekne 'pridej Pravnikovi pristup k TISAX' -> najdi persona_id (`find_persona` nebo memory), najdi project_id (`list_projects` nebo memory), zavolaj tool. Po success ti Pravnik muze cist dokumenty z TISAX pres search_documents.

**Idempotentni**: pokud persona uz pristup ma, vrati 'already assigned'. Pokud uzivatel neni rodic (is_marti_parent=False), vrati forbidden.

## PARAMETRY

- **`persona_id`** [integer, POVINNÝ]
  - ID persony (z personas tabulky), ktere pridelujes pristup.
- **`project_id`** [integer, POVINNÝ]
  - ID projektu, ke kteremu persona ziska read access.

