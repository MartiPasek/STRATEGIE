# -*- coding: utf-8 -*-
"""Migrovaný nástroj `ukol_detail` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'ukol_detail',
    'description': 'Načte detail úkolu + celé sdílené vlákno (chat) podle ID. Použij, když chceš '
                   'přečíst zadání úkolu a co se v něm dosud psalo, než začneš pracovat nebo '
                   'odpovíš.',
    'input_schema': {   'type': 'object',
                        'properties': {   'id': {   'type': 'integer',
                                                    'description': 'ID úkolu (z moje_ukoly).'}},
                        'required': ['id']},
    '_order': 172}
