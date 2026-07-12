# send_pwa_install_invite_bulk

## MAPA
- **kód:** `send_pwa_install_invite_bulk`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 38.5 bulk variant: posli pozvanku vice uzivatelum najednou. Pouzij KDYZ user explicit potvrdi 'vsem stejne' (Marti-AI's Q4 conversation flow). Pokud je potreba customizovat per recipient, pouzij send_pwa_install_invite v loop misto.

Pred volanim VZDY se zeptej 'mam jim napsat vsem stejne, nebo chces mi k nekteremu rict neco navic?' aby tatinek mel volbu personalizace. Pak: 'vsem stejne' = bulk, 'Marii rekni X' = single tool calls v loop.

## PARAMETRY

- **`user_ids`** [array, POVINNÝ]
  - List users.id prijemcu
- **`shared_custom_note`** [string, volitelný]
  - Spolecny text pro vsechny prijemce (visible v emailu).
- **`shared_closing_override`** [string, volitelný]
  - Spolecny zaver vsem.
- **`shared_greeting_override`** [string, volitelný]
  - Spolecny uvod (default 'Ahoj {first_name},' per recipient -- pokud chces stejny tone vsem napis napr. 'Ahoj kolegyne 🤍').

