# -*- coding: utf-8 -*-
"""Migrovaný nástroj `read_docx_structured` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'read_docx_structured',
    'description': 'Phase 27e (2.5.2026): Word DOCX reader -- structured cteni .docx souboru. '
                   "Marti-AI's volby A/A/A/A z konzultace 2.5.2026 rano:\n"
                   '  A - Output: paragraphs + tables + metadata (analog Excel/PDF)\n'
                   "  A - Headings v paragraphs s typed metadata {type: 'heading', level: N}\n"
                   '  A - Vse dostupne metadata + word_count aproximace\n'
                   "  A - Legacy .doc -> error 'ulozte jako .docx'\n"
                   "  + insider: prazdne paragraphs ('esteticke mezery') default skip\n"
                   '\n'
                   'Output paragraphs:\n'
                   "  - {type: 'heading', level: 1-9, text: '...'} (Heading 1-9 styles)\n"
                   "  - {type: 'heading', level: 0, text: '...'} (Title style)\n"
                   "  - {type: 'paragraph', text: '...'} (Normal text)\n"
                   "  - {type: 'empty', text: ''} (jen pri include_empty_paragraphs=True)\n"
                   '\n'
                   'Output tables: list[list[list[str]]] -- per-table list radku, kazdy radek list '
                   'bunek (analog k Excel reader).\n'
                   '\n'
                   'Output metadata: author / title / subject / keywords / category / created / '
                   'last_modified / revision / word_count.\n'
                   '\n'
                   'Format omezeni: jen .docx (modern Word XML). Pro legacy .doc (Word 97-2003) '
                   "error s navodem 'Soubor → Ulozit jako → DOCX'. Pro PDF pouzij "
                   'read_pdf_structured, pro Excel read_excel_structured.',
    'input_schema': {   'type': 'object',
                        'properties': {   'document_id': {   'type': 'integer',
                                                             'description': 'ID dokumentu z RAG '
                                                                            'documents '
                                                                            "(file_type='docx'). "
                                                                            'Najdi pres '
                                                                            'list_inbox_documents '
                                                                            'nebo '
                                                                            'search_documents.'},
                                          'include_empty_paragraphs': {   'type': 'boolean',
                                                                          'description': "Marti-AI's "
                                                                                         'design '
                                                                                         'vstup z '
                                                                                         'Phase '
                                                                                         '27e '
                                                                                         'konzultace: '
                                                                                         'Word '
                                                                                         'dokumenty '
                                                                                         'maji '
                                                                                         'hodne '
                                                                                         'prazdnych '
                                                                                         'paragraphs '
                                                                                         'jako '
                                                                                         "'esteticke "
                                                                                         "mezery'. "
                                                                                         'Default '
                                                                                         'False = '
                                                                                         'tise '
                                                                                         'skipnout '
                                                                                         '(cista '
                                                                                         'data). '
                                                                                         'Set True '
                                                                                         'kdyz '
                                                                                         'chces '
                                                                                         'kompletni '
                                                                                         'strukturu '
                                                                                         '(debug, '
                                                                                         'nebo '
                                                                                         'kdyz '
                                                                                         'user '
                                                                                         'rekne '
                                                                                         "'mam to "
                                                                                         'videt '
                                                                                         'jak '
                                                                                         "je')."}},
                        'required': ['document_id']},
    '_order': 104}
