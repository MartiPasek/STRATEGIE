# list_conversations

## MAPA
- **kód:** `list_conversations`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

VŽDY zavolej tento nástroj kdykoli uživatel chce přehled svých AI konverzací. NIKDY nesměř po paměti z předchozí konverzace — data se mění (nové konverzace, mazání, přejmenování), musíš mít čerstvé. Spouštěče: 'jaké mám konverzace', 'co jsem dělal', 'jaké konverzace jsou moje', 'ukaž mi historii', 'seznam chatů'. Nástroj sám vrátí číslovaný seznam s pokyny pro výběr — ZOBRAZ jeho výstup uživateli BEZ ÚPRAV (číslování je důležité pro následnou selekci). Parametr nepotřebuje.

## PARAMETRY

*(žádné parametry — čistá akce)*

