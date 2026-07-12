# list_recent_calls

## MAPA
- **kód:** `list_recent_calls`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Vrátí poslední hovory aktivní persony (všechny směry: přijaté, odchozí i zmeškané). Použij pro přehled všech hovorů za poslední dobu ('vsechny hovory', 'log hovoru', 'kdo mi volal dnes').

## PARAMETRY

- **`limit`** [integer, volitelný] · default: `10`
  - Max počet hovorů (default 10, max 50).

