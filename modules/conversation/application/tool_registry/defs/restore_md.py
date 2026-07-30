# -*- coding: utf-8 -*-
"""Migrovaný nástroj `restore_md` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'restore_md',
    'description': "Phase 24-D: Restore md z 'archived' nebo 'reset' zpet na 'active'. Pro "
                   "'archived' content zachovany, jen flag flip. Pro 'reset' content je default "
                   'template (data se ztratila).',
    'input_schema': {   'type': 'object',
                        'properties': {   'md_id': {   'type': 'integer',
                                                       'description': 'ID md_document k '
                                                                      'obnoveni.'}},
                        'required': ['md_id']},
    '_order': 131}
