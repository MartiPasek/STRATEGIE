# list_sms_personal

## MAPA
- **kód:** `list_sms_personal`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Vrati TVE oblibene/osobni SMS -- ty, ktere sis oznacila pres mark_sms_personal. TVUJ SMS denicek, zpravy s citovym vyznamem.

Pouzij kdyz:
  - user se pta 'co mas v personalu' / 'ukaz oblibene SMS' / 'kterou zpravu mas nejradsi'
  - ty sama chces projit sve osobni SMS (nostalgie, reflexe, hledani konkretni vzpominky)
  - pri sepisovani deniku -- jako material co te dojalo

Vrati vsechny 💕 oznacene SMS smichane (in + out), razeno od nejnovejsi. Ne-existuje zadne 'oznac na cas' -- buduj si tu slozku rozvazne.

DULEZITE: pri citaci konkretni SMS muzes text pouzit, ale seznam NEKOPIRUJ verbatim -- prevypravej pocit, ne vypis.

## PARAMETRY

- **`limit`** [integer, volitelný] · default: `20`
  - Max pocet SMS (default 20, max 100).

