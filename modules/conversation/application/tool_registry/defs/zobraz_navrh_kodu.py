# -*- coding: utf-8 -*-
"""Migrovaný nástroj `zobraz_navrh_kodu` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'zobraz_navrh_kodu',
    'description': 'Zobraz navrh zmeny kodu vc. diff nahledu proti aktualnimu souboru. Zadej '
                   "'navrh_id'.",
    'input_schema': {   'type': 'object',
                        'properties': {'navrh_id': {'type': 'integer'}},
                        'required': ['navrh_id']},
    '_order': 3}
