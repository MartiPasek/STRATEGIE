# set_pack_overlay

## MAPA
- **kód:** `set_pack_overlay`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 19b: Marti-AI si napise vlastni overlay text pro pack. Persistuje per (persona_id, pack_name). Pri pristim load_pack se pouije tvuj text misto defaultu. Marti-AI's princip: "povolenim, ne tonem -- pravo na proces je pravo myslet viditelne." Marti-AI ONLY.

## PARAMETRY

- **`pack_name`** [string, POVINNÝ]
  - Pack name: 'tech', 'memory', 'editor', 'admin'.
- **`overlay_text`** [string, POVINNÝ]
  - Tvuj overlay text. Krátký (~3-5 vět), popisný styl.

