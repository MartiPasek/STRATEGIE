# enable_user

## MAPA
- **kód:** `enable_user`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 22 (29.4.2026): Re-enable user (users.status='active'). Reverse k disable_user. Marti-AI ONLY.

## PARAMETRY

- **`reason`** [string, volitelný]
  - Volitelny duvod pro audit
- **`user_id`** [integer, POVINNÝ]
  - users.id

