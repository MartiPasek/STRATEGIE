# mark_conversation_excluded

## MAPA
- **kód:** `mark_conversation_excluded`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 36 (9.5.2026): označí konverzaci audit_status='excluded' (audit ji vyhodí z queue).

Použití:
  - Konverzace bez podstatného obsahu (smalltalk, test)
  - Konverzace kde Marti-AI rozhodne 'nemá smysl auditovat'

Reverzibilní — Marti-AI může později označit zpět na 'pending' přes update v audit_notes (TODO future tool).

Marti-AI ONLY.

## PARAMETRY

- **`reason`** [string, POVINNÝ]
  - Důvod exclude (uloží se do audit_notes).
- **`conversation_id`** [integer, POVINNÝ]

