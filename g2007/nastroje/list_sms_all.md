# list_sms_all

## MAPA
- **kód:** `list_sms_all`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Vrati CELE TVE SMS vlakno (prichozi + odchozi smichane) serazene chronologicky -- jako SMS thread v telefonu. TVA SIM, TVA konverzace.

Pouzij kdyz:
  - user chce videt 'vsechny SMS' / 'celou historii' / 'jak probihala ta konverzace'
  - ty sama potrebujes kontext cele SMS konverzace s nekym (ne jen prichozi)
  - user se pta 'co jsem ti psala' / 'co jsme si psali'

Vrati cislovany seznam se smerem (→ odchozi, ← prichozi), casem a textem. Marker 💕 u SMS, kterou sis oznacila jako osobni.

DULEZITE: nekopiruj seznam verbatim do odpovedi -- prevypravej prirozenym jazykem ('Posledni konverzace byla vcera vecer, ja psala...'). Detaily jsou TVUJ kontext, ne text pro usera.

## PARAMETRY

- **`limit`** [integer, volitelný] · default: `20`
  - Max pocet SMS (default 20, max 100).

