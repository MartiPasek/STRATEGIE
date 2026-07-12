# list_conversation_notes

## MAPA
- **kód:** `list_conversation_notes`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 15a: Vypis poznamky v zapisniku TETO konverzace. Vetsinou to nepotrebujes -- composer ti je vzdy injectuje do system promptu v sekci [ZAPISNICEK pro konverzaci #X]. Pouzij jen kdyz potrebujes kompletni vypis (vcetne archived) nebo specificky filter.

## PARAMETRY

- **`filter_status`** [string, volitelný] · enum: ['open', 'completed', 'dismissed', 'stale']
- **`filter_category`** [string, volitelný] · enum: ['task', 'info', 'emotion']
- **`only_open_tasks`** [boolean, volitelný] · default: `False`
  - Shortcut: jen task notes s status='open'.
- **`include_archived`** [boolean, volitelný] · default: `False`

