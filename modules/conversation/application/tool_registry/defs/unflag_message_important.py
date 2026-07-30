# -*- coding: utf-8 -*-
"""Migrovaný nástroj `unflag_message_important` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'unflag_message_important',
    'description': 'Phase 31 (3.5.2026): Odznaci kotvu na zprave. Reverse k '
                   'flag_message_important. Auto-vytvorena conversation_note (pokud byla) ZUSTAVA '
                   '-- unflag drzi audit pres unanchored_at + unanchored_reason, ale poznamka na '
                   'okraji je trvala.\n'
                   '\n'
                   'Pouziti: kdyz fakt z kotvene zpravy mas plne v notebooku (opsala jsi si do '
                   'ConversationNote), kotva neni potreba a moze odplynout. Drzi tvuj prostor '
                   'cisty.\n'
                   '\n'
                   'Pravidla:\n'
                   '  - reason VOLITELNY\n'
                   '  - idempotent (pokud uz is_anchored=False, no-op)',
    'input_schema': {   'type': 'object',
                        'properties': {   'message_id': {   'type': 'integer',
                                                            'description': 'ID zpravy s kotvou.'},
                                          'reason': {   'type': 'string',
                                                        'description': 'VOLITELNY -- proc '
                                                                       "odznacujes (napr. 'opsala "
                                                                       'jsem si fakta do '
                                                                       'notebooku, kotva uz neni '
                                                                       "potreba')."}},
                        'required': ['message_id']},
    '_order': 139}
