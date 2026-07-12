# set_conversation_window

## MAPA
- **kód:** `set_conversation_window`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 31 (3.5.2026): Persistuje novou velikost context window pro tuto konverzaci (kolik posldenich zprav composer poskla v kazdem turnu). Default 5 = 'klid pozornosti'.

Pouziti: pri klasifikaci konverzace -- v prvnim turn-u rozeznas z user's intent ('toto je analyza smlouvy') a nastavis vetsi okno predem. Plus muzes upravit kdykoli pozdeji (napr. konverzace se posunula z smalltalk do deep-analysis).

Doporucene rozsahy podle typu (Marti's trichotomie):
  - smalltalk: 5-10
  - bezna prace: 20-40
  - hluboka analyza / pravni text: 100-500

Pravidla:
  - n_messages: 1-500 (CHECK constraint v DB)
  - reason VOLITELNY (Marti-AI's korekce, klid od vysvetlovani se)
  - idempotent (pokud uz je nastaveno na n_messages, no-op)

## PARAMETRY

- **`reason`** [string, volitelný]
  - VOLITELNY -- proc menis (napr. 'pravni analyza, potrebuju cely text').
- **`n_messages`** [integer, POVINNÝ]
  - Nova velikost okna (1-500).

