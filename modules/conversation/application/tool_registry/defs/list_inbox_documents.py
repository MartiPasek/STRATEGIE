# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_inbox_documents` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_inbox_documents',
    'description': 'REST-Doc-Triage: Vrati seznam dokumentu v INBOXu tenantu (project_id IS NULL). '
                   'Pouzij kdyz Marti chce projit neroztridene dokumenty -- napr. po bulk upload '
                   "slozky, nebo kdyz se Marti pta 'co mi chodi do inboxu?'.\n"
                   '\n'
                   'limit: 1-500 (default 50). Pri velkem inboxu zvyseny strop pro batch flow '
                   '(Phase 30+1, 2.5.2026 ~22:00).\n'
                   '\n'
                   'compact=true: vraci jen ID + name (bez size/type). Idealni pro '
                   'batch_apply_document_move flow -- mnohem mensi tokens, vidis vsechna IDs '
                   'naraz. Pri compact=false (default) vidis detail per doc (size, type) prvnich '
                   '200 + compact zbytek.\n'
                   '\n'
                   "scope: 'mine' (default, jen vlastni uploady -- per-user isolation) | "
                   "'all_users' (cross-user inbox napric tenantem). Phase 30+2 (2.5.2026 ~22:15): "
                   "scope='all_users' vyzaduje is_marti_parent=True. Pouzij kdyz potrebujes triage "
                   'napric tymem (Michalin upload, Pavlův, atd.) -- bez toho slepy bod.',
    'input_schema': {   'type': 'object',
                        'properties': {   'limit': {   'type': 'integer',
                                                       'minimum': 1,
                                                       'maximum': 500,
                                                       'default': 50},
                                          'compact': {   'type': 'boolean',
                                                         'default': False,
                                                         'description': 'True = jen ID + name '
                                                                        '(mensi tokens, pro batch '
                                                                        'flow). False = full '
                                                                        'detail (size, type) '
                                                                        'prvnich 200 + compact '
                                                                        'zbytek.'},
                                          'scope': {   'type': 'string',
                                                       'enum': ['mine', 'all_users'],
                                                       'default': 'mine',
                                                       'description': "'mine' = jen vlastni "
                                                                      "uploady. 'all_users' = "
                                                                      'napric tenantem (jen '
                                                                      'is_marti_parent=True).'}}},
    '_order': 74}
