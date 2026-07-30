# -*- coding: utf-8 -*-
"""Migrovaný nástroj `dismiss_note` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'dismiss_note',
    'description': "Phase 15a: Vedome zrus task -- 'uz to neresim'. Pro pripady, kdy se zmenil "
                   'zamer, situace je vyresena jinak, nebo si uvedomis, ze task uz neni '
                   "relevantni. Reverzibilni pres update_note(note_id, status='open'). Validace: "
                   'jen task notes mohou byt dismissed.',
    'input_schema': {   'type': 'object',
                        'required': ['note_id'],
                        'properties': {   'note_id': {'type': 'integer'},
                                          'reason': {   'type': 'string',
                                                        'description': 'Volitelny duvod -- pripoji '
                                                                       'se k content.'}}},
    '_order': 62}
