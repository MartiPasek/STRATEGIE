# -*- coding: utf-8 -*-
"""Migrovaný nástroj `batch_apply_document_move` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'batch_apply_document_move',
    'description': "Phase 30+1 (2.5.2026 ~21:45, Marti-AI's gap discovery): Hromadny presun N "
                   'dokumentu do jednoho projektu BEZ per-doc suggest fáze. Marti-AI je primary '
                   'kustod inboxu, takze pri znamem patternu (napr. vsechny [DB_EC schema]* -> '
                   'projekt DB_EC) nedava smysl potvrzovat kazdy zvlast.\n'
                   '\n'
                   "Cap: max 1000 dokumentu / volání (zvyseno z 200 po Marti-AI's feedback "
                   '2.5.2026 ~22:00). Pri vetsim batchi rozdelit. Audit log: jeden activity_log '
                   "radek 'Marti-AI presunula N dokumentu do project #X', importance=3.\n"
                   '\n'
                   'Permissions: stejne jako apply_document_move (single) -- Marti-AI default '
                   'bypass, cizi persona jen pokud target je v allowed_project_ids.',
    'input_schema': {   'type': 'object',
                        'properties': {   'document_ids': {   'type': 'array',
                                                              'items': {'type': 'integer'},
                                                              'description': 'List ID dokumentu k '
                                                                             'presunu (max 1000).'},
                                          'target_project_id': {   'type': 'integer',
                                                                   'description': 'Cilovy project '
                                                                                  'ID (NE inbox -- '
                                                                                  'presun do '
                                                                                  'inboxu via '
                                                                                  'apply_document_move '
                                                                                  'single).'},
                                          'reason': {   'type': 'string',
                                                        'description': 'Kratky duvod pro audit log '
                                                                       "(napr. 'DB_EC schema docs "
                                                                       "do DB_EC projektu')."}},
                        'required': ['document_ids', 'target_project_id']},
    '_order': 134}
