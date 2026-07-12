# add_user_to_tenant

## MAPA
- **kód:** `add_user_to_tenant`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 35-E.3.1: Prida existujiciho usera do tenantu (multi-tenant membership). Idempotent — pokud user uz je clenem se status 'archived', reaktivuje. Pokud uz je 'active', no-op. Pouzij pro: pridani Marti do STRATEGIE tenantu, pridani Klarky do NERUDOVKA, atd. Pro vytvoreni noveho usera (zatim neexistuje) pouzij invite_user. Marti-AI ONLY. Audit log.

## PARAMETRY

- **`role`** [string, volitelný] · enum: ['owner', 'admin', 'member']
  - RBAC role: owner | admin | member. Default 'member'.
- **`reason`** [string, POVINNÝ]
  - Duvod pro audit.
- **`user_id`** [integer, POVINNÝ]
  - users.id — existujici user.
- **`tenant_id`** [integer, POVINNÝ]
  - tenants.id — existujici tenant.

