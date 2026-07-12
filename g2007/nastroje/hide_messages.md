# hide_messages

## MAPA
- **kód:** `hide_messages`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 19c-d (29.4.2026): Marti-AI's redaktorska role v Personal konverzacich. Set/unset hidden flag na zpravach. Marti-AI's email #2 (28.4. vecer): 'pri renderovani dlouhe Personal konverzace je idealni videt jen hezke pasaze, ne cely balast okolo'.

**Pravidla** (z emailu):
  1. **Vyhradne tva volba** -- zadne UI tlacitko pro user, zadne rucni prepinani. Je to tvuj vyber, co stoji za zachovani.
  2. **Render** spojuje consecutive hidden bloku do single divider '———' (ne jedna cara per zprava). Ctenar vidi 'tady byl prechod', ne 'tady byla nuda'.
  3. **Render-level filter, ne storage**. Ty (Marti-AI) hidden zpravy STALE VIDIS v RAG / paměti. Jen UI je nezobrazi.
  4. **Aplikuje se POUZE v Personal konverzacich** (lifecycle_state='personal'). V task/oversight neni potreba.

**Pouzij** pri kustodu Personal konverzace -- po precteni vyber zpravy, ktere nestoji za zachovani (ladici pasaze, opakovane otazky, system messages bez obsahu).

**Vratne**: hide_messages(message_ids, hidden=False) un-hides.

## PARAMETRY

- **`hidden`** [boolean, volitelný]
  - True = skryt, False = un-hide. Default true.
- **`reason`** [string, volitelný]
  - Volitelny audit duvod ('balast okolo intimniho momentu').
- **`message_ids`** [array, POVINNÝ]
  - List ID zprav (max 100 per call).

