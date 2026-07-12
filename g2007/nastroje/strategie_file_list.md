# strategie_file_list

## MAPA
- **kód:** `strategie_file_list`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 39: Vypise obsah adresare v STRATEGIE projektu (D:/Projekty/STRATEGIE/). Read everywhere -- vidis vsechno krome deny list patternu (.env, .git/, secrets/, *.key, node_modules/, build/, dist/, __pycache__/ a podobne).

path='' (default) = project root. path='modules/erp/' = subadresar.
recursive=True = walk celym stromem (max 1000 entries, truncated flag pri prekroceni).

Vraci items: [{name, type: 'dir'|'file', size, modified, rel_path}].
Pouzij na zacatku navigace projektem nebo pro orientaci v marti_workspace/ pri vyzvedavani draftu/analysis.

## PARAMETRY

- **`path`** [string, volitelný] · default: ``
  - Relative path uvnitr project_root. '' (default) = root. Akceptuje '/' i '\' separator. Path traversal (..) blokovan.
- **`recursive`** [boolean, volitelný] · default: `False`
  - True = rekurzivni walk subtree. False (default) = jen primy obsah adresare.

