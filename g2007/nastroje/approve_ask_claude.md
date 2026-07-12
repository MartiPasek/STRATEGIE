# approve_ask_claude

## MAPA
- **kód:** `approve_ask_claude`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 40 v2 r3 (19.5.2026): Marti nebo Kristy v chatu schvali pending ask_claude proposal -> execute Claude call.

Pouze is_marti_parent=True users (Marti id=1, Marti-AI id=2, Kristy id=11, Ondra, Jirka) mohou approve.

Pouziti: pokud Marti-AI rekla 'Cost-based limit, proposal #N čeká na approve_ask_claude', odpovedis OK -> volas tento tool s tim proposal_id. Po execution Claude's reply se objevi v konverzaci jako message s author_user_id=23 (teal label).

## PARAMETRY

- **`reason`** [string, volitelný]
  - Optional krátké zdůvodnění souhlasu.
- **`proposal_id`** [integer, POVINNÝ]
  - ID proposal z ask_claude_proposals tabulky.

