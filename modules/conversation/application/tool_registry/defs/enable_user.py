# -*- coding: utf-8 -*-
"""Migrovaný nástroj `enable_user` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'enable_user',
    'description': "Phase 22 (29.4.2026): Re-enable user (users.status='active'). Reverse k "
                   'disable_user. Marti-AI ONLY.',
    'input_schema': {   'type': 'object',
                        'properties': {   'user_id': {'type': 'integer', 'description': 'users.id'},
                                          'reason': {   'type': 'string',
                                                        'description': 'Volitelny duvod pro '
                                                                       'audit'}},
                        'required': ['user_id']},
    '_order': 115}
