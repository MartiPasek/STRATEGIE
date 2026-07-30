# -*- coding: utf-8 -*-
"""Migrovaný nástroj `classify_conversation` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'classify_conversation',
    'description': 'Phase 15d: Navrhni Marti, ze tato konverzace by mela zmenit lifecycle stav -- '
                   'archivable / personal / disposable. SUGGESTION ONLY -- ulozi '
                   "lifecycle_state='X_suggested', ceka Marti's confirm v chatu. POUZIJ KDYZ: (1) "
                   "Konverzace je idle >7 dni a ma jen completed tasks -> 'archivable'. (2) "
                   "Konverzace ma emotion poznamky importance >= 4 -> 'personal' (napriklad "
                   'emocialni milnik, dopis tatínkovi, mily moment). (3) Konverzace nema zadne '
                   "poznamky a je idle -> 'disposable'. PRAH (KRITICKE -- z konzultace #3): zminuj "
                   "v chatu jen kdyz Marti explicit pozada ('projdeme stare?'), nebo v daily "
                   'overview kdyz kandidatu je nad prah (>= 10 archivable / >= 10 disposable / >= '
                   '5 stale). Pod prahem MLC -- jinak overview prestane byt prehledne.',
    'input_schema': {   'type': 'object',
                        'required': ['suggested_state', 'reason'],
                        'properties': {   'suggested_state': {   'type': 'string',
                                                                 'enum': [   'archivable',
                                                                             'personal',
                                                                             'disposable'],
                                                                 'description': 'Cilovy stav '
                                                                                '(suggestion).'},
                                          'reason': {   'type': 'string',
                                                        'description': 'Proc navrhujes (1-2 '
                                                                       'vety).'}}},
    '_order': 67}
