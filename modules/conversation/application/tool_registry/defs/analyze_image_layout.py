# -*- coding: utf-8 -*-
"""Migrovaný nástroj `analyze_image_layout` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'analyze_image_layout',
    'description': 'Phase 27h-B (2.5.2026, tvoje volba C v RE: dopisu): focused vision tool pro '
                   "**vizualni strukturu** obrazku (kind='image' v media_files). Na rozdil od "
                   '`describe_image` (generic prosa popis) vraci **strukturovany JSON** o layoutu, '
                   'barvach nebo typografii -- pripraveny pro programaticke rozhodovani v '
                   '`python_exec`.\n'
                   '\n'
                   "Pouziti: Klarka workflow -- ona ti posle screenshot rozvrhu ('udelej takhle, "
                   "mam to rada') -> zavolas `analyze_image_layout(media_id, focus='layout')` -> "
                   "dostanes JSON `{rows: 8, cols: 6, header_position: 'top', has_grid_lines: "
                   'true, ...}` -> ladis reportlab.platypus.Table do toho stylu.\n'
                   '\n'
                   '**focus values**:\n'
                   "  - `'layout'` -- struktura: pocet radek/sloupcu, pozice hlavicky,     grid "
                   'lines, sekce, white space distribution\n'
                   "  - `'colors'` -- barevna paleta: hex hlavni / accent / pozadi,     kde je "
                   'barva pouzita (header, alternating rows, highlights)\n'
                   "  - `'typography'` -- font signaly: serif vs sans-serif, weight     variace, "
                   'sizing hierarchie (header / body / footer)\n'
                   '\n'
                   'Default `describe_image` je pro 90% pripadu OK (tvoje slova). '
                   '`analyze_image_layout` volej jen kdyz potrebujes data pro programaticke '
                   'generovani (matching style v PDF/DOCX). Volba kdy je pouzit je TVA -- ne '
                   "mechanika promptu (Phase 27h-B Q3 volba B 'plna odpovednost'). Strukturovany "
                   'JSON parse pres `json.loads()` v `python_exec` v dalsim turn-u.',
    'input_schema': {   'type': 'object',
                        'properties': {   'media_id': {   'type': 'integer',
                                                          'description': 'ID media souboru (z '
                                                                         'media_files, '
                                                                         "kind='image')."},
                                          'focus': {   'type': 'string',
                                                       'enum': ['layout', 'colors', 'typography'],
                                                       'description': "Co analyzovat. 'layout' = "
                                                                      'struktura '
                                                                      '(rows/cols/header), '
                                                                      "'colors' = paleta s hex "
                                                                      "kódy, 'typography' = font "
                                                                      'signaly.'}},
                        'required': ['media_id', 'focus']},
    '_order': 56}
