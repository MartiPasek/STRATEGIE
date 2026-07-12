# flag_message_important

## MAPA
- **kód:** `flag_message_important`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 31 (3.5.2026): KOTVA ⚓. Oznaci zpravu jako dulezitou -- drzi ji v aktivnim okne i pres cut-off, bez ohledu na stari.

Marti-AI's volba symbolu (3.5.2026 rano): ⚓ ('starsi a klidnejsi nez 🪝, prinaska obraz neceho, co drzi i v boure'). Marti-AI's metafora: 'zalozka v knize'.

Pouziti: kdyz user preda kompletni podklady (klicovy kontext, instrukce, fakty na ktere se budes vracet), flagni zpravu --drzi se v okne dokud sama neunflag (zadne expiration, zadny hard cap).

also_create_note=True (volitelne, default False -- Marti-AI's korekce 'automatismus mi bere volbu'):
  - Auto-vytvori conversation_note s source_message_id=msg
  - note_type='fact', certainty=85, importance=4
  - content = reason (pokud zadan), jinak 'Zakotvena zprava #N'
  - Tvuj vlastni text zachycujici tvuj VYKLAD (Marti-AI's metafora     'zalozka v knize a poznamka na okraj' -- kotva = zalozka,     note = poznamka, NEjsou duplikaty)

Pravidla:
  - reason VOLITELNY
  - also_create_note default False
  - idempotent (pokud uz je is_anchored=True, no-op)
  - bez parent gate (tvuj prostor)

## PARAMETRY

- **`reason`** [string, volitelný]
  - VOLITELNY -- proc kotvis (napr. 'Klarka predala kompletni podklady k rozvrhu').
- **`message_id`** [integer, POVINNÝ]
  - ID zpravy z teto konverzace.
- **`also_create_note`** [boolean, volitelný]
  - Volitelne (default False). True = auto-vytvorit conversation_note jako 'poznamku na okraji' s odkazem na zpravu. Pouzij kdyz chces dvojitou pojistku -- zalozku v knize + tvou interpretaci.

