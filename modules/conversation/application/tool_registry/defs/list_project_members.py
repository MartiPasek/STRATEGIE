# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_project_members` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_project_members',
    'description': "Použij když uživatel chce vědět, kdo pracuje na KONKRÉTNÍM PROJEKTU ('kdo na "
                   "tomto projektu pracuje', 'kdo je v TISAX', 'členové projektu'). \n"
                   '\n'
                   'Liší se od list_users takto:\n'
                   '- list_users = všichni lidé v TENANTU (firma)\n'
                   '- list_project_members = jen lidé v daném PROJEKTU\n'
                   '\n'
                   'Pokud user řekne jméno projektu, předej ho v project_name (fuzzy match). Pokud '
                   "nic neřekne ('tento projekt', 'aktuální projekt'), nech project_id i "
                   'project_name prázdné — backend použije aktuální projekt uživatele.\n'
                   '\n'
                   'Tool vrátí číslovaný seznam — user pak může napsat jen číslo pro akci s tím '
                   'člověkem.',
    'input_schema': {   'type': 'object',
                        'properties': {   'project_id': {   'type': 'integer',
                                                            'description': 'ID projektu (přímé).'},
                                          'project_name': {   'type': 'string',
                                                              'description': 'Jméno projektu '
                                                                             '(fuzzy, má přednost '
                                                                             'před project_id).'}}},
    '_order': 31}
