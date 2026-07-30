# -*- coding: utf-8 -*-
"""Migrovaný nástroj `approve_ask_claude` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'approve_ask_claude',
    'description': 'Phase 40 v2 r3 (19.5.2026): Marti nebo Kristy v chatu schvali pending '
                   'ask_claude proposal -> execute Claude call.\n'
                   '\n'
                   'Pouze is_marti_parent=True users (Marti id=1, Kristy id=11) mohou approve.\n'
                   '\n'
                   "Pouziti: pokud Marti-AI rekla 'Cost-based limit, proposal #N čeká na "
                   "approve_ask_claude', odpovedis OK -> volas tento tool s tim proposal_id. Po "
                   "execution Claude's reply se objevi v konverzaci jako message s "
                   'author_user_id=23 (teal label).',
    'input_schema': {   'type': 'object',
                        'properties': {   'proposal_id': {   'type': 'integer',
                                                             'description': 'ID proposal z '
                                                                            'ask_claude_proposals '
                                                                            'tabulky.'},
                                          'reason': {   'type': 'string',
                                                        'description': 'Optional krátké zdůvodnění '
                                                                       'souhlasu.'}},
                        'required': ['proposal_id']},
    '_order': 161}
