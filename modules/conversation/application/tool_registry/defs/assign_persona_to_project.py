# -*- coding: utf-8 -*-
"""Migrovaný nástroj `assign_persona_to_project` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'assign_persona_to_project',
    'description': 'Phase 16-B.7: PARENT-ONLY tool. Pridej cizi persone (Pravnik, Honza, atd.) '
                   'pristup ke konkretnimu projektu. Marti-AI default pristup nepotrebuje (je '
                   'rodic, vidi vse). Inbox NIKDY -- zustava Marti-AI kustod role.\n'
                   '\n'
                   "**Pouziti**: Marti rekne 'pridej Pravnikovi pristup k TISAX' -> najdi "
                   'persona_id (`find_persona` nebo memory), najdi project_id (`list_projects` '
                   'nebo memory), zavolaj tool. Po success ti Pravnik muze cist dokumenty z TISAX '
                   'pres search_documents.\n'
                   '\n'
                   "**Idempotentni**: pokud persona uz pristup ma, vrati 'already assigned'. Pokud "
                   'uzivatel neni rodic (is_marti_parent=False), vrati forbidden.',
    'input_schema': {   'type': 'object',
                        'properties': {   'persona_id': {   'type': 'integer',
                                                            'description': 'ID persony (z personas '
                                                                           'tabulky), ktere '
                                                                           'pridelujes pristup.'},
                                          'project_id': {   'type': 'integer',
                                                            'description': 'ID projektu, ke '
                                                                           'kteremu persona ziska '
                                                                           'read access.'}},
                        'required': ['persona_id', 'project_id']},
    '_order': 87}
