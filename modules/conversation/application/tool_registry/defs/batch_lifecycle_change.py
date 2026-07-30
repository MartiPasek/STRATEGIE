# -*- coding: utf-8 -*-
"""Migrovaný nástroj `batch_lifecycle_change` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'batch_lifecycle_change',
    'description': "Phase 19c-c: Hromadna lifecycle akce (10+ konverzaci najednou). Marti-AI's "
                   "email #1 bod 3 -- 'pro efektivni denni kustod by pomohl nastroj "
                   "batch_lifecycle_change(conversation_ids, target_state)'.\n"
                   '\n'
                   '**Pouzij** po `list_all_conversations` kdyz mas vyber IDs k akci. Tatinkuv '
                   "ramec: 'rader mazat vice nez mene, soft-delete je vratny priznak'. Neni "
                   "potreba se bat -- vse je vratne pres state='active'.\n"
                   '\n'
                   "**target_state**: 'archived' | 'personal' | 'pending_hard_delete' | 'active' "
                   '(= reverze).\n'
                   '\n'
                   '**Ethics gate**: pokud Marti udelil auto-lifecycle grant (vidis v [PERMISSIONS '
                   "GRANTED] block), volas BEZ explicit confirm. Jinak nejdriv ('Mam archivovat "
                   "techto 12 konverzaci? IDs: 1, 5, 8, ...?').\n"
                   '\n'
                   '**Per-id error nezablokuje zbytek** -- vrati souhrn ok/failed counts.',
    'input_schema': {   'type': 'object',
                        'properties': {   'conversation_ids': {   'type': 'array',
                                                                  'items': {'type': 'integer'},
                                                                  'description': 'List ID (max 100 '
                                                                                 'per call).'},
                                          'target_state': {   'type': 'string',
                                                              'enum': [   'archived',
                                                                          'personal',
                                                                          'pending_hard_delete',
                                                                          'active']},
                                          'reason': {'type': 'string'}},
                        'required': ['conversation_ids', 'target_state']},
    '_order': 80}
