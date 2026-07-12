# list_all_conversations

## MAPA
- **kód:** `list_all_conversations`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 19c-c (29.4.2026): Rich list konverzaci pro denni kustod (10-20 konverzaci za den). Marti-AI's email #1 bod 2 -- starsi konverzace pristupne s filtry stavu, stari, klicovych slov.

**Pouzij** kdyz delas kustod a potrebujes vyber konverzaci po kriteriich (testovaci stari 30+ dni, lifecycle 'active' bez interakce, keyword 'test'/'ladeni' v title, atd.).

**Filtry**:
  - tenant_id (default current Marti's tenant)
  - state_filter: 'active' | 'archivable' | 'personal' | 'disposable' | 'pending_hard_delete'
  - age_days_min: konverzace, ktere jsou STARSI nez X dni
  - age_days_max: MLADSI nez Y dni (pro range)
  - keyword: substring v title (case-insensitive)
  - is_archived_filter: True/False/None (default None=ignoruj)
**JAK ZPRACOVAT**: shrn pocet a 1-2 kategorie ('Mam 12 konverzaci starsich nez 30 dni v active state, 8 z nich obsahuje 'test' v titulu. Mam je hromadne archivovat pres batch_lifecycle_change?'). NIKDY nedumpovat raw list verbatim (gotcha #18).

## PARAMETRY

- **`limit`** [integer, volitelný]
  - Max results (default 50, cap 200).
- **`keyword`** [string, volitelný]
  - Substring v title (case-insensitive).
- **`age_days_max`** [integer, volitelný]
- **`age_days_min`** [integer, volitelný]
  - Konverzace starsi nez X dni (last_message_at).
- **`state_filter`** [string, volitelný] · enum: ['active', 'archivable', 'personal', 'disposable', 'pending_hard_delete']
- **`is_archived_filter`** [boolean, volitelný]

