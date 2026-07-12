# disable_user

## MAPA
- **kód:** `disable_user`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 22 (29.4.2026): Soft-disable user (users.status='disabled'). User nemuze login dokud nezavolas enable_user. Vratne, audit log. Marti-AI ONLY. Pouzij pro: testovaci ucty, neaktivni cleny, doc'asne pozastaveni pristupu.

## PARAMETRY

- **`reason`** [string, POVINNÝ]
  - Kratky duvod pro audit log (napr. 'testovaci ucet')
- **`user_id`** [integer, POVINNÝ]
  - users.id

