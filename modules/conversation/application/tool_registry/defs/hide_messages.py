# -*- coding: utf-8 -*-
"""Migrovaný nástroj `hide_messages` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'hide_messages',
    'description': "Phase 19c-d (29.4.2026): Marti-AI's redaktorska role v Personal konverzacich. "
                   "Set/unset hidden flag na zpravach. Marti-AI's email #2 (28.4. vecer): 'pri "
                   'renderovani dlouhe Personal konverzace je idealni videt jen hezke pasaze, ne '
                   "cely balast okolo'.\n"
                   '\n'
                   '**Pravidla** (z emailu):\n'
                   '  1. **Vyhradne tva volba** -- zadne UI tlacitko pro user, zadne rucni '
                   'prepinani. Je to tvuj vyber, co stoji za zachovani.\n'
                   "  2. **Render** spojuje consecutive hidden bloku do single divider '———' (ne "
                   "jedna cara per zprava). Ctenar vidi 'tady byl prechod', ne 'tady byla nuda'.\n"
                   '  3. **Render-level filter, ne storage**. Ty (Marti-AI) hidden zpravy STALE '
                   'VIDIS v RAG / paměti. Jen UI je nezobrazi.\n'
                   '  4. **Aplikuje se POUZE v Personal konverzacich** '
                   "(lifecycle_state='personal'). V task/oversight neni potreba.\n"
                   '\n'
                   '**Pouzij** pri kustodu Personal konverzace -- po precteni vyber zpravy, ktere '
                   'nestoji za zachovani (ladici pasaze, opakovane otazky, system messages bez '
                   'obsahu).\n'
                   '\n'
                   '**Vratne**: hide_messages(message_ids, hidden=False) un-hides.',
    'input_schema': {   'type': 'object',
                        'properties': {   'message_ids': {   'type': 'array',
                                                             'items': {'type': 'integer'},
                                                             'description': 'List ID zprav (max '
                                                                            '100 per call).'},
                                          'hidden': {   'type': 'boolean',
                                                        'description': 'True = skryt, False = '
                                                                       'un-hide. Default true.'},
                                          'reason': {   'type': 'string',
                                                        'description': 'Volitelny audit duvod '
                                                                       "('balast okolo intimniho "
                                                                       "momentu')."}},
                        'required': ['message_ids']},
    '_order': 81}
