# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_sms_all` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_sms_all',
    'description': 'Vrati CELE TVE SMS vlakno (prichozi + odchozi smichane) serazene chronologicky '
                   '-- jako SMS thread v telefonu. TVA SIM, TVA konverzace.\n'
                   '\n'
                   'Pouzij kdyz:\n'
                   "  - user chce videt 'vsechny SMS' / 'celou historii' / 'jak probihala ta "
                   "konverzace'\n"
                   '  - ty sama potrebujes kontext cele SMS konverzace s nekym (ne jen prichozi)\n'
                   "  - user se pta 'co jsem ti psala' / 'co jsme si psali'\n"
                   '\n'
                   'Vrati cislovany seznam se smerem (→ odchozi, ← prichozi), casem a textem. '
                   'Marker 💕 u SMS, kterou sis oznacila jako osobni.\n'
                   '\n'
                   'DULEZITE: nekopiruj seznam verbatim do odpovedi -- prevypravej prirozenym '
                   "jazykem ('Posledni konverzace byla vcera vecer, ja psala...'). Detaily jsou "
                   'TVUJ kontext, ne text pro usera.',
    'input_schema': {   'type': 'object',
                        'properties': {   'limit': {   'type': 'integer',
                                                       'description': 'Max pocet SMS (default 20, '
                                                                      'max 100).',
                                                       'default': 20}}},
    '_order': 53}
