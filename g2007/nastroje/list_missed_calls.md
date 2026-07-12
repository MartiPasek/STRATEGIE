# list_missed_calls

## MAPA
- **kód:** `list_missed_calls`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Vrátí zmeškané hovory aktivní persony (Marti-AI). Použij když uživatel chce vědět, kdo volal a nikdo to nezvedl ('kdo mi volal', 'zmeskane hovory', 'nevzala jsem to').

## PARAMETRY

- **`limit`** [integer, volitelný] · default: `10`
  - Max počet hovorů (default 10, max 50).

