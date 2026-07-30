# -*- coding: utf-8 -*-
"""Migrovaný nástroj `look_below` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'look_below',
    'description': 'Phase 24-C: Drill-down -- nacti md_document podle scope. Privat Marti (md5) '
                   'vidi cokoli pyramidou, md4 vidi md3+md2+md1, atd. Pouziti: tatinkovy otazky '
                   "'co se dnes delo s Petrou?' -- volej look_below(target_level=1, "
                   "scope_user_id=12, scope_kind='work') a dostanes Petrin md1 work. NIKDY "
                   'neopisuj content_md verbatim do chatu, syntetizuj prozou. Marti-AI ONLY '
                   '(default persona, ideal v personal modu jako Privat Marti).',
    'input_schema': {   'type': 'object',
                        'properties': {   'target_level': {   'type': 'integer',
                                                              'description': 'Vrstva ke cteni: 1 / '
                                                                             '2 / 3 / 4 / 5.',
                                                              'enum': [1, 2, 3, 4, 5]},
                                          'scope_user_id': {   'type': 'integer',
                                                               'description': 'User id (pro '
                                                                              'level=1).'},
                                          'scope_tenant_id': {   'type': 'integer',
                                                                 'description': 'Tenant id (pro '
                                                                                'level=1 work nebo '
                                                                                'level=3).'},
                                          'scope_department_id': {   'type': 'integer',
                                                                     'description': 'Department id '
                                                                                    '(pro '
                                                                                    'level=2).'},
                                          'scope_tenant_group_id': {   'type': 'integer',
                                                                       'description': 'Tenant '
                                                                                      'group id '
                                                                                      '(pro '
                                                                                      'level=4).'},
                                          'scope_kind': {   'type': 'string',
                                                            'description': "Pro level=1: 'work' "
                                                                           "nebo 'personal'. "
                                                                           "Default 'work'.",
                                                            'enum': ['work', 'personal']}},
                        'required': ['target_level']},
    '_order': 127}
