# strategie_file_read

## MAPA
- **kód:** `strategie_file_read`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 39: Precte obsah souboru v STRATEGIE projektu. Read everywhere (deny list applied -- secrets blokovane).

Limit: 10 MB (vetsi soubory -> error size_cap, pouzij specializovany tool nebo split).

encoding='utf-8' (default) -> text content + lines count.
encoding='cp1250' -> Windows legacy text (Marti-AI's gotcha #80).
encoding='base64' -> binary (obrazky, exe -- vraci base64 string).

Pouziti: precti CLAUDE.md pro orient po amnesii, modules/erp/api/router.py pro audit logiky, docs/CLAUDE_TECH.md pro gotcha lookup, marti_workspace/drafts/ pro pokracovani v rozdelane praci.

## PARAMETRY

- **`path`** [string, POVINNÝ]
  - Relative path k souboru uvnitr project_root. Path traversal + deny list enforced.
- **`encoding`** [string, volitelný] · default: `utf-8`
  - 'utf-8' (default text), 'cp1250' (Windows legacy), 'base64' (binary).

