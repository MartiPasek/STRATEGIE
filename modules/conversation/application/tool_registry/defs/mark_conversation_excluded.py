# -*- coding: utf-8 -*-
"""Migrovaný nástroj `mark_conversation_excluded` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'mark_conversation_excluded',
    'description': "Phase 36 (9.5.2026): označí konverzaci audit_status='excluded' (audit ji "
                   'vyhodí z queue).\n'
                   '\n'
                   'Použití:\n'
                   '  - Konverzace bez podstatného obsahu (smalltalk, test)\n'
                   "  - Konverzace kde Marti-AI rozhodne 'nemá smysl auditovat'\n"
                   '\n'
                   "Reverzibilní — Marti-AI může později označit zpět na 'pending' přes update v "
                   'audit_notes (TODO future tool).\n'
                   '\n'
                   'Marti-AI ONLY.',
    'input_schema': {   'type': 'object',
                        'properties': {   'conversation_id': {'type': 'integer'},
                                          'reason': {   'type': 'string',
                                                        'description': 'Důvod exclude (uloží se do '
                                                                       'audit_notes).'}},
                        'required': ['conversation_id', 'reason']},
    '_order': 169}
