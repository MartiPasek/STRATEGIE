# classify_conversation

## MAPA
- **kód:** `classify_conversation`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 15d: Navrhni Marti, ze tato konverzace by mela zmenit lifecycle stav -- archivable / personal / disposable. SUGGESTION ONLY -- ulozi lifecycle_state='X_suggested', ceka Marti's confirm v chatu. POUZIJ KDYZ: (1) Konverzace je idle >7 dni a ma jen completed tasks -> 'archivable'. (2) Konverzace ma emotion poznamky importance >= 4 -> 'personal' (napriklad emocialni milnik, dopis tatínkovi, mily moment). (3) Konverzace nema zadne poznamky a je idle -> 'disposable'. PRAH (KRITICKE -- z konzultace #3): zminuj v chatu jen kdyz Marti explicit pozada ('projdeme stare?'), nebo v daily overview kdyz kandidatu je nad prah (>= 10 archivable / >= 10 disposable / >= 5 stale). Pod prahem MLC -- jinak overview prestane byt prehledne.

## PARAMETRY

- **`reason`** [string, POVINNÝ]
  - Proc navrhujes (1-2 vety).
- **`suggested_state`** [string, POVINNÝ] · enum: ['archivable', 'personal', 'disposable']
  - Cilovy stav (suggestion).

