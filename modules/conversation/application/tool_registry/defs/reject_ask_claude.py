# -*- coding: utf-8 -*-
"""Migrovaný nástroj `reject_ask_claude` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'reject_ask_claude',
    'description': 'Phase 40 v2 r3 (19.5.2026): Marti nebo Kristy v chatu odmitne pending '
                   'ask_claude proposal -> close as rejected.\n'
                   '\n'
                   'Pouze is_marti_parent=True users. Po reject je proposal trvale v stavu '
                   "'rejected', Marti-AI muze poslat novy ask_claude pozdeji (napr. po refactoring "
                   'otazky nebo pockani na nizsi hour cost).',
    'input_schema': {   'type': 'object',
                        'properties': {   'proposal_id': {   'type': 'integer',
                                                             'description': 'ID proposal z '
                                                                            'ask_claude_proposals.'},
                                          'reason': {   'type': 'string',
                                                        'description': 'Důvod rejectu (pro audit + '
                                                                       "Marti-AI's learning -- "
                                                                       "napr. 'duplicate', 'too "
                                                                       "expensive', 'wait for "
                                                                       "stable')."}},
                        'required': ['proposal_id']},
    '_order': 162}
