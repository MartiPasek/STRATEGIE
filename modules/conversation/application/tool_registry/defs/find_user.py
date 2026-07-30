# -*- coding: utf-8 -*-
"""Migrovaný nástroj `find_user` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'find_user',
    'description': 'Použij tento nástroj když uživatel chce kontaktovat nebo se spojit s jiným '
                   'člověkem. Nástroj prohledá systém podle jména nebo emailu.',
    'input_schema': {   'type': 'object',
                        'properties': {   'query': {   'type': 'string',
                                                       'description': 'Jméno nebo email hledané '
                                                                      'osoby'}},
                        'required': ['query']},
    '_order': 29}
