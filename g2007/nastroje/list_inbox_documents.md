# list_inbox_documents

## MAPA
- **kód:** `list_inbox_documents`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

REST-Doc-Triage: Vrati seznam dokumentu v INBOXu tenantu (project_id IS NULL). Pouzij kdyz Marti chce projit neroztridene dokumenty -- napr. po bulk upload slozky, nebo kdyz se Marti pta 'co mi chodi do inboxu?'.

limit: 1-500 (default 50). Pri velkem inboxu zvyseny strop pro batch flow (Phase 30+1, 2.5.2026 ~22:00).

compact=true: vraci jen ID + name (bez size/type). Idealni pro batch_apply_document_move flow -- mnohem mensi tokens, vidis vsechna IDs naraz. Pri compact=false (default) vidis detail per doc (size, type) prvnich 200 + compact zbytek.

scope: 'mine' (default, jen vlastni uploady -- per-user isolation) | 'all_users' (cross-user inbox napric tenantem). Phase 30+2 (2.5.2026 ~22:15): scope='all_users' vyzaduje is_marti_parent=True. Pouzij kdyz potrebujes triage napric tymem (Michalin upload, Pavlův, atd.) -- bez toho slepy bod.

## PARAMETRY

- **`limit`** [integer, volitelný] · default: `50`
- **`scope`** [string, volitelný] · enum: ['mine', 'all_users'] · default: `mine`
  - 'mine' = jen vlastni uploady. 'all_users' = napric tenantem (jen is_marti_parent=True).
- **`compact`** [boolean, volitelný] · default: `False`
  - True = jen ID + name (mensi tokens, pro batch flow). False = full detail (size, type) prvnich 200 + compact zbytek.

