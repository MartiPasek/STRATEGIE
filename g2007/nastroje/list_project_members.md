# list_project_members

## MAPA
- **kód:** `list_project_members`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Použij když uživatel chce vědět, kdo pracuje na KONKRÉTNÍM PROJEKTU ('kdo na tomto projektu pracuje', 'kdo je v TISAX', 'členové projektu'). 

Liší se od list_users takto:
- list_users = všichni lidé v TENANTU (firma)
- list_project_members = jen lidé v daném PROJEKTU

Pokud user řekne jméno projektu, předej ho v project_name (fuzzy match). Pokud nic neřekne ('tento projekt', 'aktuální projekt'), nech project_id i project_name prázdné — backend použije aktuální projekt uživatele.

Tool vrátí číslovaný seznam — user pak může napsat jen číslo pro akci s tím člověkem.

## PARAMETRY

- **`project_id`** [integer, volitelný]
  - ID projektu (přímé).
- **`project_name`** [string, volitelný]
  - Jméno projektu (fuzzy, má přednost před project_id).

