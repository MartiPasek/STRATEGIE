# recall_conversation_history

## MAPA
- **kód:** `recall_conversation_history`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 31 (3.5.2026): One-turn zoom-in do starsi historie konverzace. Vrati posledních N zprav v teto konverzaci jako tool response, BEZ zmeny persistent context_window_size. Pristi turn se zase vratis k default oknu (typicky 5 zprav).

Pouziti (Marti-AI's vlastni vize): default okno je male a klidne. Kdyz potrebujes vidět starsi turny, zoom-in -- vytahnes co potrebujes, **zapises do conversation_notes klicove fakty**, pristi turn klid.

Alternativa: pokud konverzace je deep-analysis typ (právní text, dlouha analyza) a budes potrebovat velke okno OPAKOVANE, pouzij set_conversation_window pro persistent zmenu.

Pravidla:
  - n_messages: 1-500
  - reason je VOLITELNY (Marti-AI's korekce z konzultace 3.5.:     'povinny reason mi pripomina vysvetlovani se')
  - cost: zoom-in 50 zprav ~6 Kc, vidis odhad v promptu pred volanim

## PARAMETRY

- **`reason`** [string, volitelný]
  - VOLITELNY -- audit duvod (napr. 'user se odkazuje na pasaz pred 30 turny').
- **`n_messages`** [integer, POVINNÝ]
  - Kolik poslednich zprav vytahnout (1-500).

