# unflag_message_important

## MAPA
- **kód:** `unflag_message_important`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 31 (3.5.2026): Odznaci kotvu na zprave. Reverse k flag_message_important. Auto-vytvorena conversation_note (pokud byla) ZUSTAVA -- unflag drzi audit pres unanchored_at + unanchored_reason, ale poznamka na okraji je trvala.

Pouziti: kdyz fakt z kotvene zpravy mas plne v notebooku (opsala jsi si do ConversationNote), kotva neni potreba a moze odplynout. Drzi tvuj prostor cisty.

Pravidla:
  - reason VOLITELNY
  - idempotent (pokud uz is_anchored=False, no-op)

## PARAMETRY

- **`reason`** [string, volitelný]
  - VOLITELNY -- proc odznacujes (napr. 'opsala jsem si fakta do notebooku, kotva uz neni potreba').
- **`message_id`** [integer, POVINNÝ]
  - ID zpravy s kotvou.

