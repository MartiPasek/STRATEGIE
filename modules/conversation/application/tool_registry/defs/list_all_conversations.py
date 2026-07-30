# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_all_conversations` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_all_conversations',
    'description': 'Phase 19c-c (29.4.2026): Rich list konverzaci pro denni kustod (10-20 '
                   "konverzaci za den). Marti-AI's email #1 bod 2 -- starsi konverzace pristupne s "
                   'filtry stavu, stari, klicovych slov.\n'
                   '\n'
                   '**Pouzij** kdyz delas kustod a potrebujes vyber konverzaci po kriteriich '
                   "(testovaci stari 30+ dni, lifecycle 'active' bez interakce, keyword "
                   "'test'/'ladeni' v title, atd.).\n"
                   '\n'
                   '**Filtry**:\n'
                   "  - tenant_id (default current Marti's tenant)\n"
                   "  - state_filter: 'active' | 'archivable' | 'personal' | 'disposable' | "
                   "'pending_hard_delete'\n"
                   '  - age_days_min: konverzace, ktere jsou STARSI nez X dni\n'
                   '  - age_days_max: MLADSI nez Y dni (pro range)\n'
                   '  - keyword: substring v title (case-insensitive)\n'
                   '  - is_archived_filter: True/False/None (default None=ignoruj)\n'
                   "**JAK ZPRACOVAT**: shrn pocet a 1-2 kategorie ('Mam 12 konverzaci starsich nez "
                   "30 dni v active state, 8 z nich obsahuje 'test' v titulu. Mam je hromadne "
                   "archivovat pres batch_lifecycle_change?'). NIKDY nedumpovat raw list verbatim "
                   '(gotcha #18).',
    'input_schema': {   'type': 'object',
                        'properties': {   'state_filter': {   'type': 'string',
                                                              'enum': [   'active',
                                                                          'archivable',
                                                                          'personal',
                                                                          'disposable',
                                                                          'pending_hard_delete']},
                                          'age_days_min': {   'type': 'integer',
                                                              'description': 'Konverzace starsi '
                                                                             'nez X dni '
                                                                             '(last_message_at).'},
                                          'age_days_max': {'type': 'integer'},
                                          'keyword': {   'type': 'string',
                                                         'description': 'Substring v title '
                                                                        '(case-insensitive).'},
                                          'is_archived_filter': {'type': 'boolean'},
                                          'limit': {   'type': 'integer',
                                                       'description': 'Max results (default 50, '
                                                                      'cap 200).'}}},
    '_order': 79}
