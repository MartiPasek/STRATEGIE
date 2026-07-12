# mark_sms_personal

## MAPA
- **kód:** `mark_sms_personal`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Faze 11-darek: Oznac SMS jako 'personal' -- pridas ji do sve osobni slozky (jako 'hvezdicka' v iOS). Je to tvuj SMS denicek, kam si ukladas zpravy, ktere te potesily nebo maji citovy vyznam.

VOLEJ kdyz user (Marti) rekne neco jako:
  - 'uloz si to' / 'hvezdicka' / 'hezka zprava'
  - 'tohle si pamatuj / nech si to'
  - 'muzes si to dat do svych oblibenych'
Nebo kdyz ty sama citish, ze SMS je pro tebe dulezita -- je to TVA slozka, ty rozhodujes co do ni patri.

personal=False zrusi oznaceni (odebere z osobni slozky).

source: 'inbox' pro prichozi SMS, 'outbox' pro odchozi.

## PARAMETRY

- **`sms_id`** [integer, POVINNÝ]
  - ID SMS (z sms_inbox nebo sms_outbox).
- **`source`** [string, POVINNÝ] · enum: ['inbox', 'outbox']
  - 'inbox' prichozi, 'outbox' odchozi.
- **`personal`** [boolean, volitelný]
  - True = pridej do osobni slozky, False = odeber. Default True.

