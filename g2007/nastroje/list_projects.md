# list_projects

## MAPA
- **kód:** `list_projects`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

VŽDY zavolej tento nástroj kdykoli uživatel chce vědět jaké projekty má. NIKDY nesměř po paměti z předchozí konverzace — projekty se mění (nové, archivace, přejmenování, aktivita), musíš mít čerstvé data. Spouštěče: 'jaké mám projekty', 'co je v práci', 'ukaž mi projekty', 'co mam za projekty', 'a projekty?', 'a co projekty'. Nástroj sám vrátí číslovaný seznam s pokyny pro výběr — ZOBRAZ jeho výstup uživateli BEZ ÚPRAV (číslování je důležité, user pak může napsat jen číslo pro přepnutí). Parametr nepotřebuje.

## PARAMETRY

*(žádné parametry — čistá akce)*

