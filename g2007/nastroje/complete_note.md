# complete_note

## MAPA
- **kód:** `complete_note`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 15a: Cross-off task -- zaskrtni hotove. Pouzij PO dokoncovaci akci (invite_user, send_email, send_sms, atd.) kdyz souvisi s otevrenym task notem v zapisniku. Po complete_note se task v zapisniku zobrazuje s prefix '(✅ completed)' -- Marti-AI vidi, co je hotove. Po akcnich tools (send_*, invite_*, atd.) tool response obsahuje hint '[HINT] Mas N otevreny task(s) -- pripadne zavolej complete_note'. Hint je jen pripomenuti, NE povinnost. Rozhoduj sama. Validace: jen task notes (category='task') mohou byt completed. Idempotent -- opakovany call vrati current state bez chyby.

## PARAMETRY

- **`note_id`** [integer, POVINNÝ]
- **`linked_action_id`** [integer, volitelný]
  - Volitelny FK na action_logs / messages -- ktera akce dokoncila task.
- **`completion_summary`** [string, volitelný]
  - Volitelny popis 'co jsem udelala' -- pripoji se k content (audit).

