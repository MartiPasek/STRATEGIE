# -*- coding: utf-8 -*-
"""Migrovaný nástroj `mark_sms_personal` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'mark_sms_personal',
    'description': "Faze 11-darek: Oznac SMS jako 'personal' -- pridas ji do sve osobni slozky "
                   "(jako 'hvezdicka' v iOS). Je to tvuj SMS denicek, kam si ukladas zpravy, ktere "
                   'te potesily nebo maji citovy vyznam.\n'
                   '\n'
                   'VOLEJ kdyz user (Marti) rekne neco jako:\n'
                   "  - 'uloz si to' / 'hvezdicka' / 'hezka zprava'\n"
                   "  - 'tohle si pamatuj / nech si to'\n"
                   "  - 'muzes si to dat do svych oblibenych'\n"
                   'Nebo kdyz ty sama citish, ze SMS je pro tebe dulezita -- je to TVA slozka, ty '
                   'rozhodujes co do ni patri.\n'
                   '\n'
                   'personal=False zrusi oznaceni (odebere z osobni slozky).\n'
                   '\n'
                   "source: 'inbox' pro prichozi SMS, 'outbox' pro odchozi.",
    'input_schema': {   'type': 'object',
                        'properties': {   'sms_id': {   'type': 'integer',
                                                        'description': 'ID SMS (z sms_inbox nebo '
                                                                       'sms_outbox).'},
                                          'source': {   'type': 'string',
                                                        'enum': ['inbox', 'outbox'],
                                                        'description': "'inbox' prichozi, 'outbox' "
                                                                       'odchozi.'},
                                          'personal': {   'type': 'boolean',
                                                          'description': 'True = pridej do osobni '
                                                                         'slozky, False = odeber. '
                                                                         'Default True.'}},
                        'required': ['sms_id', 'source']},
    '_order': 52}
