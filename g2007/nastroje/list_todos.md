# list_todos

## MAPA
- **kód:** `list_todos`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Vrati nezdokoncene todo ukoly aktivniho uzivatele. Pouzij kdyz user rekne 'ukaz mi todo', 'co mam za ukoly', 'co treba todo' v kontextu daily overview, nebo kdyz po 'pojdeme na todo' Marti-AI chce nabidnout konkretni ukoly k projeti.

Vraci cislovany seznam s content (text ukolu) a created_at. Default scope = aktualni user (Marti). Pro vsechny v tenantu / cross-tenant pouzij dalsi parametry recall_thoughts (rodicovsky bypass).

ROZDIL od recall_thoughts: list_todos filtruje TYPE='todo' a NOT done. recall_thoughts hleda paměť o entitě (Petrovi, projektu) -- pro projeti todo listu je tento tool primarni.

## PARAMETRY

- **`limit`** [integer, volitelný] · default: `10`
  - Max pocet todo (default 10).

