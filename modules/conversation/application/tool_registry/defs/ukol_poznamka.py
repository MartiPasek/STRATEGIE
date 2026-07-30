# -*- coding: utf-8 -*-
"""Migrovaný nástroj `ukol_poznamka` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'ukol_poznamka',
    'description': 'Napíše zprávu do sdíleného vlákna úkolu = TVŮJ report zpátky zadavateli. Buď '
                   'konkrétní: co jsi udělala, výsledek (ID, počet řádků, varování). Zadavatel a u '
                   'tvých úkolů i rodiče dostanou notifikaci na mobil.',
    'input_schema': {   'type': 'object',
                        'properties': {   'id': {'type': 'integer', 'description': 'ID úkolu.'},
                                          'text': {   'type': 'string',
                                                      'description': 'Text zprávy do vlákna.'}},
                        'required': ['id', 'text']},
    '_order': 173}
