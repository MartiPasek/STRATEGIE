# -*- coding: utf-8 -*-
"""Migrovaný nástroj `remove_project_member` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'remove_project_member',
    'description': "Použij když uživatel chce odebrat někoho z projektu ('odeber Kláru z "
                   "projektu', 'smaz ji z TISAX'). Symetrické s add_project_member: podporuje "
                   'project_id nebo project_name (fuzzy). User se může odebrat i sám sebe (opustit '
                   'projekt) — to pak stačí jakékoli jeho členství. Owner projektu nelze odebrat '
                   '(nejdříve převést vlastnictví).',
    'input_schema': {   'type': 'object',
                        'properties': {   'target_user_id': {   'type': 'integer',
                                                                'description': 'ID uživatele k '
                                                                               'odebrání'},
                                          'project_id': {   'type': 'integer',
                                                            'description': 'ID projektu'},
                                          'project_name': {   'type': 'string',
                                                              'description': 'Jméno projektu '
                                                                             '(fuzzy, má přednost '
                                                                             'před project_id)'}},
                        'required': ['target_user_id']},
    '_order': 33}
