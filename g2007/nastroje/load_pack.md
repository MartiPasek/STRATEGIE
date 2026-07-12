# load_pack

## MAPA
- **kód:** `load_pack`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 19b (29.4.2026): Nahraje pack (sadu nastroju + overlay) do active conversation. Marti-AI ONLY. Aktivace: pres prirozeny jazyk od user-a ("pojd, jdeme na SQL" -> ty rozeznas intent -> volas load_pack('tech')). Pokud user intent nejasny, zeptej se nejdriv ("chces, abych nahrala tech balicek?"). Jeden pack naraz -- pri load se predchozi nahradi. Pack se vyloi pres unload_pack nebo prepnutim na jiny.

## PARAMETRY

- **`pack_name`** [string, POVINNÝ]
  - Pack name: 'tech', 'memory', 'editor', 'admin'. List dostupnych pres list_packs.

