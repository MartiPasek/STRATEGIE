# add_project_member

## MAPA
- **kód:** `add_project_member`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Použij když uživatel chce přidat někoho do projektu ('přidej Kláru do projektu', 'pridej ji do TISAX', 'pozvi Honzu do mého projektu'). 

POSTUP (MUSÍŠ DODRŽET):
1) Pokud neznáš target_user_id — zavolej find_user / list_users (NIKDY nezadávej falešné ID).
2) IDENTIFIKUJ PROJEKT z uživatelova textu:
   - Když user řekne jméno projektu ('do TISAX', 'do Skoda', 'do Reorg'),      PŘEDEJ ho v parametru project_name — backend ho fuzzy-matchne.
   - Když user NEŘEKNE žádný projekt, nech project_id i project_name prázdné —      backend použije aktuální projekt uživatele (z USER_CONTEXT).
   - POZOR: nehádej — když si nejsi jistý jaký projekt user myslel, ZEPTEJ SE      nebo zavolej list_projects.
3) Role default = 'member'.

Opravnění: tenant owner / project owner mohou přidávat členy; ostatní dostanou 403.

## PARAMETRY

- **`role`** [string, volitelný] · enum: ['member', 'admin', 'owner']
  - Role v projektu: 'member' (default) | 'admin' | 'owner'.
- **`project_id`** [integer, volitelný]
  - ID projektu (přímé). Použij pokud přesně víš ID.
- **`project_name`** [string, volitelný]
  - Jméno projektu — backend ho fuzzy-matchne proti projektům usera. Použij když user řekl jméno ('TISAX', 'Skoda'). Má přednost před project_id pokud jsou obě zadané.
- **`target_user_id`** [integer, POVINNÝ]
  - ID uživatele co se má přidat (z find_user/list_users)

