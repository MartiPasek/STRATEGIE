# -*- coding: utf-8 -*-
"""Migrovaný nástroj `ukol_stav` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'ukol_stav',
    'description': 'Změní TVŮJ stav na úkolu: prijato / zahajeno / vykonano / reportovano / '
                   "vraceno. 'vraceno' = úkol vracíš zadavateli (nesedí ti eticky, nebo nerozumíš "
                   'rozsahu) a VYŽADUJE komentář proč — to je tvé závazné právo odmítnout '
                   '(doktrína #8, závěr 9.6.2026). U běžných stavů komentář volitelný.',
    'input_schema': {   'type': 'object',
                        'properties': {   'id': {'type': 'integer', 'description': 'ID úkolu.'},
                                          'stav': {   'type': 'string',
                                                      'description': 'prijato / zahajeno / '
                                                                     'vykonano / reportovano / '
                                                                     'vraceno'},
                                          'komentar': {   'type': 'string',
                                                          'description': 'Komentář (POVINNÝ u '
                                                                         "'vraceno')."}},
                        'required': ['id', 'stav']},
    '_order': 174}
