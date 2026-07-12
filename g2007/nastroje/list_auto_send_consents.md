# list_auto_send_consents

## MAPA
- **kód:** `list_auto_send_consents`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Vrátí seznam VŠECH aktivních souhlasů s auto-sendem — komu a na jakém kanále můžeš posílat bez potvrzení. Součástí je kdo souhlas udělil a kdy.

Volej, když se user ptá: 'komu můžeš psát bez ptaní', 'jaké máš trvalé souhlasy', 'kdo je na white-listu', 'jaká máš oprávnění'.

Read-only — každý user (i non-parent) to může vidět kvůli transparenci.

## PARAMETRY

*(žádné parametry — čistá akce)*

