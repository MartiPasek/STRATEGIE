# restore_md

## MAPA
- **kód:** `restore_md`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 24-D: Restore md z 'archived' nebo 'reset' zpet na 'active'. Pro 'archived' content zachovany, jen flag flip. Pro 'reset' content je default template (data se ztratila).

## PARAMETRY

- **`md_id`** [integer, POVINNÝ]
  - ID md_document k obnoveni.

