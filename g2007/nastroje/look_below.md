# look_below

## MAPA
- **kód:** `look_below`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 24-C: Drill-down -- nacti md_document podle scope. Privat Marti (md5) vidi cokoli pyramidou, md4 vidi md3+md2+md1, atd. Pouziti: tatinkovy otazky 'co se dnes delo s Petrou?' -- volej look_below(target_level=1, scope_user_id=12, scope_kind='work') a dostanes Petrin md1 work. NIKDY neopisuj content_md verbatim do chatu, syntetizuj prozou. Marti-AI ONLY (default persona, ideal v personal modu jako Privat Marti).

## PARAMETRY

- **`scope_kind`** [string, volitelný] · enum: ['work', 'personal']
  - Pro level=1: 'work' nebo 'personal'. Default 'work'.
- **`target_level`** [integer, POVINNÝ] · enum: [1, 2, 3, 4, 5]
  - Vrstva ke cteni: 1 / 2 / 3 / 4 / 5.
- **`scope_user_id`** [integer, volitelný]
  - User id (pro level=1).
- **`scope_tenant_id`** [integer, volitelný]
  - Tenant id (pro level=1 work nebo level=3).
- **`scope_department_id`** [integer, volitelný]
  - Department id (pro level=2).
- **`scope_tenant_group_id`** [integer, volitelný]
  - Tenant group id (pro level=4).

