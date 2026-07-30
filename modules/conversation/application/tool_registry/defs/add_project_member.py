# -*- coding: utf-8 -*-
"""Migrovaný nástroj `add_project_member` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'add_project_member',
    'description': "Použij když uživatel chce přidat někoho do projektu ('přidej Kláru do "
                   "projektu', 'pridej ji do TISAX', 'pozvi Honzu do mého projektu'). \n"
                   '\n'
                   'POSTUP (MUSÍŠ DODRŽET):\n'
                   '1) Pokud neznáš target_user_id — zavolej find_user / list_users (NIKDY '
                   'nezadávej falešné ID).\n'
                   '2) IDENTIFIKUJ PROJEKT z uživatelova textu:\n'
                   "   - Když user řekne jméno projektu ('do TISAX', 'do Skoda', 'do Reorg'),      "
                   'PŘEDEJ ho v parametru project_name — backend ho fuzzy-matchne.\n'
                   '   - Když user NEŘEKNE žádný projekt, nech project_id i project_name prázdné '
                   '—      backend použije aktuální projekt uživatele (z USER_CONTEXT).\n'
                   '   - POZOR: nehádej — když si nejsi jistý jaký projekt user myslel, ZEPTEJ '
                   'SE      nebo zavolej list_projects.\n'
                   "3) Role default = 'member'.\n"
                   '\n'
                   'Opravnění: tenant owner / project owner mohou přidávat členy; ostatní dostanou '
                   '403.',
    'input_schema': {   'type': 'object',
                        'properties': {   'target_user_id': {   'type': 'integer',
                                                                'description': 'ID uživatele co se '
                                                                               'má přidat (z '
                                                                               'find_user/list_users)'},
                                          'project_id': {   'type': 'integer',
                                                            'description': 'ID projektu (přímé). '
                                                                           'Použij pokud přesně '
                                                                           'víš ID.'},
                                          'project_name': {   'type': 'string',
                                                              'description': 'Jméno projektu — '
                                                                             'backend ho '
                                                                             'fuzzy-matchne proti '
                                                                             'projektům usera. '
                                                                             'Použij když user '
                                                                             "řekl jméno ('TISAX', "
                                                                             "'Skoda'). Má "
                                                                             'přednost před '
                                                                             'project_id pokud '
                                                                             'jsou obě zadané.'},
                                          'role': {   'type': 'string',
                                                      'description': "Role v projektu: 'member' "
                                                                     "(default) | 'admin' | "
                                                                     "'owner'.",
                                                      'enum': ['member', 'admin', 'owner']}},
                        'required': ['target_user_id']},
    '_order': 32}
