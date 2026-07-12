# create_tenant

## MAPA
- **kód:** `create_tenant`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 35-E.3.1: Vytvori novy tenant. Auto-prida volajiciho usera (nebo specified owner_user_id) jako 'owner' clena. tenant_code idealne uppercase ASCII (EUROSOFT, STRATEGIE, NERUDOVKA). tenant_type: 'system' (interni framework, e.g. STRATEGIE), 'company' (firma, e.g. EUROSOFT), 'school' (NERUDOVKA), 'family', 'project', 'personal'. Marti-AI ONLY. Audit log v activity_log.

## PARAMETRY

- **`reason`** [string, POVINNÝ]
  - Duvod pro audit (proc novy tenant).
- **`tenant_code`** [string, POVINNÝ]
  - Kratky uppercase identifier (max 100 char, ASCII). Pouziva se v UI jako pilulka. Napr. 'STRATEGIE'.
- **`tenant_name`** [string, POVINNÝ]
  - Display jmeno tenantu (max 255 char). Napr. 'STRATEGIE'.
- **`tenant_type`** [string, POVINNÝ] · enum: ['system', 'company', 'school', 'family', 'project', 'personal']
  - system | company | school | family | project | personal
- **`owner_user_id`** [integer, volitelný]
  - Volitelne: users.id vlastnika tenantu. Default = volajici user (Marti).

