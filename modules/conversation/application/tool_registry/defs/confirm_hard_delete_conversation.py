# -*- coding: utf-8 -*-
"""Migrovaný nástroj `confirm_hard_delete_conversation` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'confirm_hard_delete_conversation',
    'description': "Phase 15e: Trvale smazani konverzace. POUZIJ JEN PO Marti's explicit 'smaz "
                   "trvale konverzaci #X' v chatu. Konverzace MUSI byt v "
                   "lifecycle_state='pending_hard_delete' (= archived + 90d). DESTRUKTIVNI: smaze "
                   'messages, conversation_notes, summaries, shares, participants, '
                   'project_history. Reverze NENI mozna. ETIKA: pouzivej extremne opatrne. Pokud '
                   "Marti rekne 'smaz' bez 'trvale', radeji se zeptej zda mysli archive nebo "
                   'trvale. Personal konverzace IMMUNE. Plus backend ma parent gate.',
    'input_schema': {   'type': 'object',
                        'required': ['target_conversation_id', 'confirm_phrase'],
                        'properties': {   'target_conversation_id': {   'type': 'integer',
                                                                        'description': 'ID '
                                                                                       'konverzace '
                                                                                       'ke '
                                                                                       'smazani.'},
                                          'confirm_phrase': {   'type': 'string',
                                                                'description': "Cely text Marti's "
                                                                               'confirm vety -- '
                                                                               'audit trail.'}}},
    '_order': 72}
