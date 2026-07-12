# list_selected_documents

## MAPA
- **kód:** `list_selected_documents`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

**TENTO NASTROJ POUZIJ** kdykoli se uzivatel zminí o 'oznacenych souborech', 'vybranych dokumentech', 'tom co jsem oznacil', 'oznaceny seznam' nebo podobne. User si v Files modalu vybral skupinu dokumentu pres Ctrl/Shift+klik (per-user selection persisting napric session) a chce aby s nimi neco udelal.

VRACI: pocet + IDs + struktura per projekt (kolik kde). NEPISH verbatim seznam (Sonnet rad opisuje) -- pouzi to k formulaci prozaicke odpovedi v 1. osobe (napr. 'Mas oznacenych 5 souboru: 3 v projektu SKOLA a 2 v inboxu. Co s nimi mam udelat?').

DALE: pred jakoukoliv akci (smazat, presunout) MUSIS uzivateli shrnout, co se stane, a CEKAT na confirm v chatu ('ano smaz' / 'ano presun do X'). Az pak volej `apply_to_selection`.

## PARAMETRY

*(žádné parametry — čistá akce)*

