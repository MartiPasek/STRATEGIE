# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_excel_sheets` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_excel_sheets',
    'description': 'Phase 27a (1.5.2026): Excel reader - krok 1 metadata. Vrati seznam vsech listu '
                   'v xlsx souboru s pocet radku, sloupcu a preview prvnich headers. Pouziti: kdyz '
                   'user nahraje xlsx (pres email attachment auto-import nebo drag&drop), nejdriv '
                   'volej tento tool, abys videla kolik je tam listu a jak se jmenuji. Pak cilene '
                   "volas read_excel_structured pro konkretni list. Marti-AI's design (RE: dopis "
                   "1.5.2026): 'Plna kontrola > pohodli. Jeden velky response s 2000 radky napric "
                   "listy by byl zbytecna zatez.' Funguje pro .xlsx a .xlsm; legacy .xls "
                   'nepodporovan (vyzaduje konverzi).',
    'input_schema': {   'type': 'object',
                        'properties': {   'document_id': {   'type': 'integer',
                                                             'description': 'ID dokumentu z RAG '
                                                                            'documents tabulky. '
                                                                            'Najdi ho pres '
                                                                            'list_inbox_documents '
                                                                            'nebo search_documents '
                                                                            "(file_type='xlsx')."}},
                        'required': ['document_id']},
    '_order': 97}
