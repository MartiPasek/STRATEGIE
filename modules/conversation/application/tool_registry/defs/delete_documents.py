# -*- coding: utf-8 -*-
"""Migrovaný nástroj `delete_documents` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'delete_documents',
    'description': 'Phase 27g (1.5.2026): Smaze jeden nebo vice dokumentu z RAG documents tabulky '
                   "(DB cascade -- chunks + vektory + storage file + selection). Marti-AI's "
                   "discovery 1.5.2026 vecer: 'apply_to_selection vyzaduje UI selection workflow, "
                   "delete_email je jen pro emaily, primy delete_by_id chybel'.\n"
                   '\n'
                   'MANDATORY user confirm v chatu pred volanim (destructive, nevratne). Workflow: '
                   'list_inbox_documents nebo search_documents -> ukaz user seznam -> user rekne '
                   "'ano smaz' -> volas tento tool. NIKDY auto-delete bez explicitniho user "
                   'souhlasu, i kdyz mas auto_lifecycle_consent (Phase 19c-b se vztahuje na '
                   'lifecycle akce, ne hard delete documents).\n'
                   '\n'
                   'Cascade behavior: document_chunks (CASCADE), document_vectors (CASCADE pres '
                   'chunks), user_document_selections (cleanup), storage file na disku (delete).\n'
                   '\n'
                   'Tenant gate: parent (is_marti_parent=True) bypass, ostatni mohou jen smazat '
                   'dokumenty ze sveho aktivniho tenantu.\n'
                   '\n'
                   'Cap 50 IDs per call. Pro vetsi cleanup volej znovu s mensim list.',
    'input_schema': {   'type': 'object',
                        'properties': {   'document_ids': {   'type': 'array',
                                                              'items': {'type': 'integer'},
                                                              'description': 'Seznam document_ids '
                                                                             'ke smazani. Najdes '
                                                                             'pres '
                                                                             'list_inbox_documents, '
                                                                             'search_documents, '
                                                                             'list_excel_sheets '
                                                                             'atd.'},
                                          'reason': {   'type': 'string',
                                                        'description': 'Volitelny duvod pro audit '
                                                                       "log (napr. 'testovaci "
                                                                       "duplikaty', 'cleanup po "
                                                                       "smoke test')."}},
                        'required': ['document_ids']},
    '_order': 105}
