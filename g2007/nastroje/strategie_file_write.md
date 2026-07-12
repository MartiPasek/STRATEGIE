# strategie_file_write

## MAPA
- **kód:** `strategie_file_write`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 39: Zapise soubor do marti_workspace/** (write zone whitelist). Mimo marti_workspace/ -> 403 write_zone_violation.

Limit: 5 MB per call (pro vetsi obsah split na vice souboru).

Doctrine (Marti-AI's chat 19.5. 02:30):
  - marti_workspace/drafts/ -- rozepsane myslenky (NE RAG ingest)
  - marti_workspace/analysis/ -- hotove analyzy (auto-RAG ingest)
  - marti_workspace/output/ -- hotove vystupy k presunu/commit (auto-RAG)
  - marti_workspace/notes/ -- scratch pad 'pokracuj od radku 847' (NE RAG)
  - marti_workspace/claude_chats/ -- Phase 40 v2 transcripty (auto-RAG)

Naming convention: _vN pro versions (foo_v1.txt, foo_v2.txt) -- last-write-wins, no lock.

mode='overwrite' (default), 'append', 'fail_if_exists'.
encoding='utf-8' (default), 'base64' (binary).

## PARAMETRY

- **`mode`** [string, volitelný] · enum: ['overwrite', 'append', 'fail_if_exists'] · default: `overwrite`
  - 'overwrite' (default) = replace existing. 'append' = add to end (vytvori pokud neexistuje). 'fail_if_exists' = error pokud target uz existuje (safety pro draft preservation).
- **`path`** [string, POVINNÝ]
  - Relative path UVNITR marti_workspace/. Path traversal + deny list + write zone enforced.
- **`content`** [string, POVINNÝ]
  - Obsah souboru. Pro text encoding='utf-8' default, pro binary encoding='base64' a content = base64 string.
- **`encoding`** [string, volitelný] · default: `utf-8`
  - 'utf-8' (default text) nebo 'base64' (binary).

