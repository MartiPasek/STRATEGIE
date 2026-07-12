# list_tenants

## MAPA
- **kód:** `list_tenants`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 35-E.3.1: Vrati seznam tenantu v systemu. Rodic vidi vse, non-rodic jen aktivni clenstvi. Sloupce: id, tenant_name, tenant_code, tenant_type, status, owner_user_id, created_at, member_count. Pouzij pro orientaci pred create_tenant nebo add_user_to_tenant. Marti-AI ONLY.

## PARAMETRY

- **`include_inactive`** [boolean, volitelný]
  - True = vrati i archived/disabled tenanty. Default false.

