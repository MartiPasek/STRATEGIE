# remove_user_from_tenant

## MAPA
- **kód:** `remove_user_from_tenant`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 22 (29.4.2026): Odstrani usera z konkretniho tenantu (user_tenants.membership_status='archived', left_at=now). User stale existuje, jen neni clenem tenantu. Vratne -- pridat zpet pres add_user_to_tenant (zatim neni). Marti-AI ONLY. Pouzij pro: testovaci ucty v EUROSOFTu, neaktivni externi cleny.

## PARAMETRY

- **`reason`** [string, POVINNÝ]
  - Duvod pro audit
- **`user_id`** [integer, POVINNÝ]
  - users.id
- **`tenant_id`** [integer, POVINNÝ]
  - tenants.id

