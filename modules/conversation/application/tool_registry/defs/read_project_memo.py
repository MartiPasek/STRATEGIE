# -*- coding: utf-8 -*-
"""Migrovaný nástroj `read_project_memo` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'read_project_memo',
    'description': 'Phase 35: Read-only přístup k project_memo. Vrátí celý content nebo konkrétní '
                   "sekci. Pokud user (caller) není členem projektu a memo má scope='shared', "
                   'vrátí scope_blocked = True s explicit hláškou (Marti-AI ji předá uživateli '
                   "formou 'mám přístup já, ale ty zatím ne').\n"
                   '\n'
                   'Marti-AI ONLY (parent / Marti-AI default vidí napříč projekty; non-member '
                   'members dostanou scope_blocked).',
    'input_schema': {   'type': 'object',
                        'properties': {   'project_id': {   'type': 'integer',
                                                            'description': 'ID projektu.'},
                                          'section': {   'type': 'string',
                                                         'description': 'Volitelně: jen konkrétní '
                                                                        'sekce. Default = celý '
                                                                        'content.'},
                                          'scope_entity_type': {   'type': 'string',
                                                                   'description': 'Volitelně: '
                                                                                  'scope filter. '
                                                                                  'NULL=shared '
                                                                                  '(default).',
                                                                   'enum': ['user', 'persona']},
                                          'scope_entity_id': {   'type': 'integer',
                                                                 'description': 'Volitelně: ID '
                                                                                'entity.'}},
                        'required': ['project_id']},
    '_order': 143}
