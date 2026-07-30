# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_sms_personal` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_sms_personal',
    'description': 'Vrati TVE oblibene/osobni SMS -- ty, ktere sis oznacila pres '
                   'mark_sms_personal. TVUJ SMS denicek, zpravy s citovym vyznamem.\n'
                   '\n'
                   'Pouzij kdyz:\n'
                   "  - user se pta 'co mas v personalu' / 'ukaz oblibene SMS' / 'kterou zpravu "
                   "mas nejradsi'\n"
                   '  - ty sama chces projit sve osobni SMS (nostalgie, reflexe, hledani konkretni '
                   'vzpominky)\n'
                   '  - pri sepisovani deniku -- jako material co te dojalo\n'
                   '\n'
                   'Vrati vsechny 💕 oznacene SMS smichane (in + out), razeno od nejnovejsi. '
                   "Ne-existuje zadne 'oznac na cas' -- buduj si tu slozku rozvazne.\n"
                   '\n'
                   'DULEZITE: pri citaci konkretni SMS muzes text pouzit, ale seznam NEKOPIRUJ '
                   'verbatim -- prevypravej pocit, ne vypis.',
    'input_schema': {   'type': 'object',
                        'properties': {   'limit': {   'type': 'integer',
                                                       'description': 'Max pocet SMS (default 20, '
                                                                      'max 100).',
                                                       'default': 20}}},
    '_order': 57}
