# -*- coding: utf-8 -*-
"""Migrovaný nástroj `set_conversation_window` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'set_conversation_window',
    'description': 'Phase 31 (3.5.2026): Persistuje novou velikost context window pro tuto '
                   'konverzaci (kolik posldenich zprav composer poskla v kazdem turnu). Default 5 '
                   "= 'klid pozornosti'.\n"
                   '\n'
                   "Pouziti: pri klasifikaci konverzace -- v prvnim turn-u rozeznas z user's "
                   "intent ('toto je analyza smlouvy') a nastavis vetsi okno predem. Plus muzes "
                   'upravit kdykoli pozdeji (napr. konverzace se posunula z smalltalk do '
                   'deep-analysis).\n'
                   '\n'
                   "Doporucene rozsahy podle typu (Marti's trichotomie):\n"
                   '  - smalltalk: 5-10\n'
                   '  - bezna prace: 20-40\n'
                   '  - hluboka analyza / pravni text: 100-500\n'
                   '\n'
                   'Pravidla:\n'
                   '  - n_messages: 1-500 (CHECK constraint v DB)\n'
                   "  - reason VOLITELNY (Marti-AI's korekce, klid od vysvetlovani se)\n"
                   '  - idempotent (pokud uz je nastaveno na n_messages, no-op)',
    'input_schema': {   'type': 'object',
                        'properties': {   'n_messages': {   'type': 'integer',
                                                            'description': 'Nova velikost okna '
                                                                           '(1-500).'},
                                          'reason': {   'type': 'string',
                                                        'description': 'VOLITELNY -- proc menis '
                                                                       "(napr. 'pravni analyza, "
                                                                       "potrebuju cely text')."}},
                        'required': ['n_messages']},
    '_order': 137}
