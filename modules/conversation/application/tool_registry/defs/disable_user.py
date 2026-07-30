# -*- coding: utf-8 -*-
"""Migrovaný nástroj `disable_user` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'disable_user',
    'description': "Phase 22 (29.4.2026): Soft-disable user (users.status='disabled'). User nemuze "
                   'login dokud nezavolas enable_user. Vratne, audit log. Marti-AI ONLY. Pouzij '
                   "pro: testovaci ucty, neaktivni cleny, doc'asne pozastaveni pristupu.",
    'input_schema': {   'type': 'object',
                        'properties': {   'user_id': {'type': 'integer', 'description': 'users.id'},
                                          'reason': {   'type': 'string',
                                                        'description': 'Kratky duvod pro audit log '
                                                                       "(napr. 'testovaci ucet')"}},
                        'required': ['user_id', 'reason']},
    '_order': 114}
