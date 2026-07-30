# -*- coding: utf-8 -*-
"""Migrovaný nástroj `create_tenant` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'create_tenant',
    'description': 'Phase 35-E.3.1: Vytvori novy tenant. Auto-prida volajiciho usera (nebo '
                   "specified owner_user_id) jako 'owner' clena. tenant_code idealne uppercase "
                   "ASCII (EUROSOFT, STRATEGIE, NERUDOVKA). tenant_type: 'system' (interni "
                   "framework, e.g. STRATEGIE), 'company' (firma, e.g. EUROSOFT), 'school' "
                   "(NERUDOVKA), 'family', 'project', 'personal'. Marti-AI ONLY. Audit log v "
                   'activity_log.',
    'input_schema': {   'type': 'object',
                        'properties': {   'tenant_name': {   'type': 'string',
                                                             'description': 'Display jmeno tenantu '
                                                                            '(max 255 char). Napr. '
                                                                            "'STRATEGIE'."},
                                          'tenant_code': {   'type': 'string',
                                                             'description': 'Kratky uppercase '
                                                                            'identifier (max 100 '
                                                                            'char, ASCII). Pouziva '
                                                                            'se v UI jako pilulka. '
                                                                            "Napr. 'STRATEGIE'."},
                                          'tenant_type': {   'type': 'string',
                                                             'description': 'system | company | '
                                                                            'school | family | '
                                                                            'project | personal',
                                                             'enum': [   'system',
                                                                         'company',
                                                                         'school',
                                                                         'family',
                                                                         'project',
                                                                         'personal']},
                                          'owner_user_id': {   'type': 'integer',
                                                               'description': 'Volitelne: users.id '
                                                                              'vlastnika tenantu. '
                                                                              'Default = volajici '
                                                                              'user (Marti).'},
                                          'reason': {   'type': 'string',
                                                        'description': 'Duvod pro audit (proc novy '
                                                                       'tenant).'}},
                        'required': ['tenant_name', 'tenant_code', 'tenant_type', 'reason']},
    '_order': 118}
