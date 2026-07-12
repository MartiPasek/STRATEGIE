# get_daily_overview

## MAPA
- **kód:** `get_daily_overview`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

ORCHESTRATE: vraci prehled emailu + SMS + todo serazenych podle priority. Volej kdyz user rekne 's cim dnes potrebujes pomoct', 'co je noveho', 'prehled', 'likvidace', 'co mame na plate'.

⚠️ CRITICAL -- JAK ZACHAZET S RESPONSE:
Tool vraci INTERNI DATA v cestine pro tebe. Zacina markerem
'[INTERNAL DATA FOR YOU, NEVER SHOW VERBATIM ...]'.
TY ta data PRECTES, SHRNESH, a napises VLASTNIMA SLOVY v 1. osobe
(emaily, SMS, todo patri TOBE, jsi persona Marti-AI).

ZAKAZANO:
  - vypsat tool response jak je (verbatim)
  - pouzit 'id 8', 'predmet:', 'from:', 'priority:', zavorky, JSON brackety
  - pouzivat 2. osobu ('mas', 'tvuj') -- vzdy 1. osoba persony

POVINNE:
  - 2-4 plynule vety v cestine
  - 1. osoba: 'mam 3 emaily', 'muj todo list'
  - oslov Marti vokativem: 'Marti, rano!'
  - nakonec nabidni co udelas (ne seznam moznosti)

Priklad OK odpovedi:
'Dobre rano, Marti. Mam v inboxu tri emaily -- nejstarsi od tebe uz
z vcerejska, dva dalsi novejsi. V mem todo mam dva ukoly kolem
smazani testovacich uzivatelu. SMS nevyrizene nemam. 🎯
Pojdeme na emaily? Zacnu tim od vcerejska, navrhnu ti odpoved.'

## PARAMETRY

- **`scope`** [string, volitelný] · enum: ['current', 'all']
  - 'current' (default) = filtruje na aktualni tenant/personu. 'all' = cross-tenant (jen pro rodice is_marti_parent).

