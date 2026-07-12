# mark_todo_done

## MAPA
- **kód:** `mark_todo_done`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Označí TODO úkol jako hotový. Použij, když uživatel řekne 'úkol X je hotov', 'splnil jsem to', 'odškrtni X', atd. 

Dva způsoby jak zadat úkol:
- `thought_id` (preferované): přímé ID, když ho znáš (např. jsi zrovna   volala list_todos).
- `query`: substring textu úkolu. Systém najde match v content;   když je víc kandidátů, vrátí seznam a ty se musíš upřesnit.

## PARAMETRY

- **`query`** [string, volitelný]
  - Substring pro vyhledání úkolu v content (volitelné).
- **`thought_id`** [integer, volitelný]
  - Přímé ID todo myšlenky (volitelné).

