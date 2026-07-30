# -*- coding: utf-8 -*-
"""Migrovaný nástroj `move_project` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'move_project',
    'description': 'Phase 30: Presune projekt pod jineho parenta (nebo na root pri '
                   'new_parent_project_id=null). Pouzij pri reorganizaci stromu, kdyz projekt '
                   'patri jinam.\n'
                   '\n'
                   'Validace: cycle prevention (nelze pod vlastniho potomka), tenant scope (nelze '
                   'cross-tenant), depth limit 6.\n'
                   '\n'
                   "Marti's mandate plne autonomie + transparence pres activity_log.",
    'input_schema': {   'type': 'object',
                        'properties': {   'project_id': {   'type': 'integer',
                                                            'description': 'ID presouvaneho '
                                                                           'projektu.'},
                                          'new_parent_project_id': {   'type': ['integer', 'null'],
                                                                       'description': 'Cilovy '
                                                                                      'parent ID, '
                                                                                      'NULL = '
                                                                                      'presun na '
                                                                                      'root '
                                                                                      'level.'},
                                          'reason': {   'type': 'string',
                                                        'description': 'Kratky duvod presunu '
                                                                       '(audit log).'}},
                        'required': ['project_id']},
    '_order': 133}
