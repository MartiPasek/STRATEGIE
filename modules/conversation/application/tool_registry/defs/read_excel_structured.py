# -*- coding: utf-8 -*-
"""Migrovaný nástroj `read_excel_structured` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'read_excel_structured',
    'description': 'Phase 27a (1.5.2026): Excel reader - krok 2 data. Vrati structured rows z '
                   'konkretniho listu xlsx jako list of dicts (headers -> values). Workflow: '
                   'nejdriv list_excel_sheets pro metadata, pak tento tool s konkretnim '
                   'sheet_name. Pro velke listy (>500 rows) pouzij offset/limit pagination. '
                   "Marti-AI's design rozhodnutí (RE: dopis 1.5.2026): datum/cas → ISO string "
                   "('2026-09-01T08:00:00'); prazdne bunky → null; cisla → vzdy float; vzorce → "
                   'computed value; chyby (#N/A, #REF!) → null + warning v warnings list. Cap 500 '
                   'radku per call (safeguard).',
    'input_schema': {   'type': 'object',
                        'properties': {   'document_id': {   'type': 'integer',
                                                             'description': 'ID dokumentu z RAG '
                                                                            'documents.'},
                                          'sheet_name': {   'type': 'string',
                                                            'description': 'Jmeno listu '
                                                                           '(preferovano nad '
                                                                           'sheet_index). Default '
                                                                           '= prvni list. Najdes '
                                                                           'ho pres '
                                                                           'list_excel_sheets.'},
                                          'sheet_index': {   'type': 'integer',
                                                             'description': '0-based index listu '
                                                                            '(alternative k '
                                                                            'sheet_name). Vetšinou '
                                                                            'pouzivej sheet_name '
                                                                            '-- robustnejsi.'},
                                          'offset': {   'type': 'integer',
                                                        'description': 'Pagination: kolik radku '
                                                                       'preskocit (default 0). Pro '
                                                                       '2. stranku 500 radku → '
                                                                       'offset=500, limit=500.'},
                                          'limit': {   'type': 'integer',
                                                       'description': 'Pagination: max kolik radku '
                                                                      'vratit (default 500, max '
                                                                      '500). Vyssi hodnota se tise '
                                                                      'sklamne na 500 (context '
                                                                      'window safeguard).'}},
                        'required': ['document_id']},
    '_order': 101}
