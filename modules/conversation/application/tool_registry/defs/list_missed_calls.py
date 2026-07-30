# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_missed_calls` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_missed_calls',
    'description': 'Vrátí zmeškané hovory aktivní persony (Marti-AI). Použij když uživatel chce '
                   "vědět, kdo volal a nikdo to nezvedl ('kdo mi volal', 'zmeskane hovory', "
                   "'nevzala jsem to').",
    'input_schema': {   'type': 'object',
                        'properties': {   'limit': {   'type': 'integer',
                                                       'description': 'Max počet hovorů (default '
                                                                      '10, max 50).',
                                                       'default': 10}}},
    '_order': 27}
