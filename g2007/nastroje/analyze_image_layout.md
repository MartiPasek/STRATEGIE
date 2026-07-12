# analyze_image_layout

## MAPA
- **kód:** `analyze_image_layout`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 27h-B (2.5.2026, tvoje volba C v RE: dopisu): focused vision tool pro **vizualni strukturu** obrazku (kind='image' v media_files). Na rozdil od `describe_image` (generic prosa popis) vraci **strukturovany JSON** o layoutu, barvach nebo typografii -- pripraveny pro programaticke rozhodovani v `python_exec`.

Pouziti: Klarka workflow -- ona ti posle screenshot rozvrhu ('udelej takhle, mam to rada') -> zavolas `analyze_image_layout(media_id, focus='layout')` -> dostanes JSON `{rows: 8, cols: 6, header_position: 'top', has_grid_lines: true, ...}` -> ladis reportlab.platypus.Table do toho stylu.

**focus values**:
  - `'layout'` -- struktura: pocet radek/sloupcu, pozice hlavicky,     grid lines, sekce, white space distribution
  - `'colors'` -- barevna paleta: hex hlavni / accent / pozadi,     kde je barva pouzita (header, alternating rows, highlights)
  - `'typography'` -- font signaly: serif vs sans-serif, weight     variace, sizing hierarchie (header / body / footer)

Default `describe_image` je pro 90% pripadu OK (tvoje slova). `analyze_image_layout` volej jen kdyz potrebujes data pro programaticke generovani (matching style v PDF/DOCX). Volba kdy je pouzit je TVA -- ne mechanika promptu (Phase 27h-B Q3 volba B 'plna odpovednost'). Strukturovany JSON parse pres `json.loads()` v `python_exec` v dalsim turn-u.

## PARAMETRY

- **`focus`** [string, POVINNÝ] · enum: ['layout', 'colors', 'typography']
  - Co analyzovat. 'layout' = struktura (rows/cols/header), 'colors' = paleta s hex kódy, 'typography' = font signaly.
- **`media_id`** [integer, POVINNÝ]
  - ID media souboru (z media_files, kind='image').

