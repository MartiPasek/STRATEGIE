# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_navrhy_kodu` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_navrhy_kodu',
    'description': "Vypis cekajici navrhy zmen kodu (stav 'navrzen').",
    'input_schema': {'type': 'object', 'properties': {}},
    '_order': 2}
