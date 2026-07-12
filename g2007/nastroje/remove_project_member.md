# remove_project_member

## MAPA
- **kód:** `remove_project_member`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Použij když uživatel chce odebrat někoho z projektu ('odeber Kláru z projektu', 'smaz ji z TISAX'). Symetrické s add_project_member: podporuje project_id nebo project_name (fuzzy). User se může odebrat i sám sebe (opustit projekt) — to pak stačí jakékoli jeho členství. Owner projektu nelze odebrat (nejdříve převést vlastnictví).

## PARAMETRY

- **`project_id`** [integer, volitelný]
  - ID projektu
- **`project_name`** [string, volitelný]
  - Jméno projektu (fuzzy, má přednost před project_id)
- **`target_user_id`** [integer, POVINNÝ]
  - ID uživatele k odebrání

