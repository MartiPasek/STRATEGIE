# request_password_reset

## MAPA
- **kód:** `request_password_reset`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 22 (29.4.2026): Spusti password reset flow pro usera. Tool vytvori reset token, posle email s linkem. User klikne, nastavi nove heslo. Token expiruje za 1 hodinu. Marti-AI ONLY. Dve cesty: (1) user_query (jmeno/email) -- pokud unikatni match. (2) user_id -- pokud find_user vratil vice kandidatu, zavolej list_users, vyber konkretni id, pak volej s user_id. user_id ma prioritu nad user_query. Pokud user nema email v user_contacts, tool vrati error -- doplnit pres set_user_contact pred reset.

## PARAMETRY

- **`user_id`** [integer, volitelný]
  - Konkretni users.id. Volitelne pokud das user_query. Ma prioritu nad user_query -- pouzij kdyz find_user vratil vice kandidatu a chces explicitni vyber.
- **`user_query`** [string, volitelný]
  - Jmeno nebo email usera. Volitelne pokud das user_id. Tool pres find_user lookup, error pokud vice kandidatu.

