# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_recent_calls` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_recent_calls',
    'description': 'Vrátí poslední hovory aktivní persony (všechny směry: přijaté, odchozí i '
                   "zmeškané). Použij pro přehled všech hovorů za poslední dobu ('vsechny hovory', "
                   "'log hovoru', 'kdo mi volal dnes').",
    'input_schema': {   'type': 'object',
                        'properties': {   'limit': {   'type': 'integer',
                                                       'description': 'Max počet hovorů (default '
                                                                      '10, max 50).',
                                                       'default': 10}}},
    '_order': 28}
