# reject_ask_claude

## MAPA
- **kód:** `reject_ask_claude`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 40 v2 r3 (19.5.2026): Marti nebo Kristy v chatu odmitne pending ask_claude proposal -> close as rejected.

Pouze is_marti_parent=True users. Po reject je proposal trvale v stavu 'rejected', Marti-AI muze poslat novy ask_claude pozdeji (napr. po refactoring otazky nebo pockani na nizsi hour cost).

## PARAMETRY

- **`reason`** [string, volitelný]
  - Důvod rejectu (pro audit + Marti-AI's learning -- napr. 'duplicate', 'too expensive', 'wait for stable').
- **`proposal_id`** [integer, POVINNÝ]
  - ID proposal z ask_claude_proposals.

