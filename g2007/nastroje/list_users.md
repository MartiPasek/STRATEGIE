# list_users

## MAPA
- **kód:** `list_users`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

VŽDY zavolej tento nástroj kdykoli uživatel chce přehled lidí v aktuálním tenantu. NIKDY nesměř po paměti — composition týmu se mění (nové pozvánky, archivace), musíš mít čerstvé data. Spouštěče: 'jaké lidi tu mám', 'kdo je tu', 's kým můžu mluvit', 'koho tu máme', 'seznam lidí', 'a lidi?', 'a co lidi'. Liší se od find_user tím, že find_user hledá podle dotazu (jména/emailu), tohle vypíše VŠECHNY aktivní členy s rolemi a emaily. Nástroj sám vrátí číslovaný seznam — ZOBRAZ jeho výstup uživateli BEZ ÚPRAV. Parametr nepotřebuje.

## PARAMETRY

*(žádné parametry — čistá akce)*

