# -*- coding: utf-8 -*-
"""Migrovaný nástroj `schval_zmenu_kodu` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'schval_zmenu_kodu',
    'description': '[JEN RODIC] Schval a NASAD navrh zmeny kodu (zapis + commit + push + restart). '
                   "Zadej 'navrh_id'.",
    'input_schema': {   'type': 'object',
                        'properties': {'navrh_id': {'type': 'integer'}},
                        'required': ['navrh_id']},
    '_order': 4}
