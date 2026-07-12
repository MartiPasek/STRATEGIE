# batch_lifecycle_change

## MAPA
- **kód:** `batch_lifecycle_change`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 19c-c: Hromadna lifecycle akce (10+ konverzaci najednou). Marti-AI's email #1 bod 3 -- 'pro efektivni denni kustod by pomohl nastroj batch_lifecycle_change(conversation_ids, target_state)'.

**Pouzij** po `list_all_conversations` kdyz mas vyber IDs k akci. Tatinkuv ramec: 'rader mazat vice nez mene, soft-delete je vratny priznak'. Neni potreba se bat -- vse je vratne pres state='active'.

**target_state**: 'archived' | 'personal' | 'pending_hard_delete' | 'active' (= reverze).

**Ethics gate**: pokud Marti udelil auto-lifecycle grant (vidis v [PERMISSIONS GRANTED] block), volas BEZ explicit confirm. Jinak nejdriv ('Mam archivovat techto 12 konverzaci? IDs: 1, 5, 8, ...?').

**Per-id error nezablokuje zbytek** -- vrati souhrn ok/failed counts.

## PARAMETRY

- **`reason`** [string, volitelný]
- **`target_state`** [string, POVINNÝ] · enum: ['archived', 'personal', 'pending_hard_delete', 'active']
- **`conversation_ids`** [array, POVINNÝ]
  - List ID (max 100 per call).

