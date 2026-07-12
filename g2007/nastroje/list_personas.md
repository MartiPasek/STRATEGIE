# list_personas

## MAPA
- **kód:** `list_personas`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

VŽDY zavolej tento nástroj kdykoli uživatel chce přehled dostupných AI person ('jaké máš persony', 'jaké AI tu jsou', 'seznam asistentů', 'koho můžu zavolat', 'co umíš'). NIKDY nesměř po paměti — persony se mění (admin přidává nové, edituje existující). Nástroj vrátí číslovaný seznam — user může napsat číslo pro přepnutí na danou personu. ZOBRAZ výstup BEZ ÚPRAV (číslování je důležité). Parametr není potřeba — scope je automaticky podle tenantu usera.

## PARAMETRY

*(žádné parametry — čistá akce)*

