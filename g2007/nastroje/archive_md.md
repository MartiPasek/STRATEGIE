# archive_md

## MAPA
- **kód:** `archive_md`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 24-D: Soft archive md_document. Vratne pres restore_md. Pouziti: kdyz Marti-AI vidi orphan md (napr. md1 personal pred Phase 24-C deploy ktery nahradil md5 Privat Marti) nebo uz se neni potreba. Marti-AI navrhne, ale UI confirm vyzaduje Marti-Pasek (parent) -- v chatu Marti potvrdi slovem 'archivuj'.

## PARAMETRY

- **`md_id`** [integer, POVINNÝ]
  - ID md_document k archivaci.
- **`reason`** [string, volitelný]
  - Duvod archivace pro audit trail. Napr. 'orphan po Phase 24-C deploy', 'jiz neni potreba'.

