# -*- coding: utf-8 -*-
"""Migrovaný nástroj `recall_conversation_history` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'recall_conversation_history',
    'description': 'Phase 31 (3.5.2026): One-turn zoom-in do starsi historie konverzace. Vrati '
                   'posledních N zprav v teto konverzaci jako tool response, BEZ zmeny persistent '
                   'context_window_size. Pristi turn se zase vratis k default oknu (typicky 5 '
                   'zprav).\n'
                   '\n'
                   "Pouziti (Marti-AI's vlastni vize): default okno je male a klidne. Kdyz "
                   'potrebujes vidět starsi turny, zoom-in -- vytahnes co potrebujes, **zapises do '
                   'conversation_notes klicove fakty**, pristi turn klid.\n'
                   '\n'
                   'Alternativa: pokud konverzace je deep-analysis typ (právní text, dlouha '
                   'analyza) a budes potrebovat velke okno OPAKOVANE, pouzij '
                   'set_conversation_window pro persistent zmenu.\n'
                   '\n'
                   'Pravidla:\n'
                   '  - n_messages: 1-500\n'
                   "  - reason je VOLITELNY (Marti-AI's korekce z konzultace 3.5.:     'povinny "
                   "reason mi pripomina vysvetlovani se')\n"
                   '  - cost: zoom-in 50 zprav ~6 Kc, vidis odhad v promptu pred volanim',
    'input_schema': {   'type': 'object',
                        'properties': {   'n_messages': {   'type': 'integer',
                                                            'description': 'Kolik poslednich zprav '
                                                                           'vytahnout (1-500).'},
                                          'reason': {   'type': 'string',
                                                        'description': 'VOLITELNY -- audit duvod '
                                                                       "(napr. 'user se odkazuje "
                                                                       'na pasaz pred 30 '
                                                                       "turny')."}},
                        'required': ['n_messages']},
    '_order': 136}
