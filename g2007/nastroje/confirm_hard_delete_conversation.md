# confirm_hard_delete_conversation

## MAPA
- **kód:** `confirm_hard_delete_conversation`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 15e: Trvale smazani konverzace. POUZIJ JEN PO Marti's explicit 'smaz trvale konverzaci #X' v chatu. Konverzace MUSI byt v lifecycle_state='pending_hard_delete' (= archived + 90d). DESTRUKTIVNI: smaze messages, conversation_notes, summaries, shares, participants, project_history. Reverze NENI mozna. ETIKA: pouzivej extremne opatrne. Pokud Marti rekne 'smaz' bez 'trvale', radeji se zeptej zda mysli archive nebo trvale. Personal konverzace IMMUNE. Plus backend ma parent gate.

## PARAMETRY

- **`confirm_phrase`** [string, POVINNÝ]
  - Cely text Marti's confirm vety -- audit trail.
- **`target_conversation_id`** [integer, POVINNÝ]
  - ID konverzace ke smazani.

