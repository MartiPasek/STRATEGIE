# -*- coding: utf-8 -*-
"""Migrovaný nástroj `review_my_calls` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'review_my_calls',
    'description': 'Faze 10: Vraci agregaty LLM volani (tokeny, cena v USD, latence) napric tvou '
                   'historii -- kolik jsi ty (Marti-AI) dnes / za tyden / za mesic spotrebovala. '
                   "Pouzij kdyz user rekne: 'kolik me dnes stalo', 'kolik tokenu za tyden', 'kolik "
                   "EUROSOFT propalil', 'kde nejvic utikaji penize', 'jak jsem drahou AI'.\n"
                   '\n'
                   'ETHICAL: vraci se jen AGREGATY (sumy + counts + prumery), ne raw '
                   'request/response JSON. Raw detail jde prohlizet v Dev View modalu v UI, ne v '
                   'chatu -- admin si to otevre kliknutim na lupu.\n'
                   '\n'
                   "Defaultne scope='today' a tenant='current' (aktualni tenant konverzace). Rodic "
                   "(is_marti_parent) muze pouzit filter_tenant='all' pro cross-tenant pohled.",
    'input_schema': {   'type': 'object',
                        'properties': {   'scope': {   'type': 'string',
                                                       'enum': ['today', 'week', 'month', 'all'],
                                                       'description': 'Casovy rozsah (default: '
                                                                      'today).'},
                                          'aggregate_by': {   'type': 'string',
                                                              'enum': [   'kind',
                                                                          'day',
                                                                          'tenant',
                                                                          'user',
                                                                          'persona',
                                                                          'model'],
                                                              'description': 'Podle ceho seskupit '
                                                                             'radky (default: '
                                                                             'kind).'},
                                          'filter_kind': {   'type': 'string',
                                                             'description': 'Jen jeden kind: '
                                                                            'router / composer / '
                                                                            'title / summary / '
                                                                            'email_suggest / '
                                                                            'sms_task / '
                                                                            'question_gen / '
                                                                            'answer_review. '
                                                                            'Default: vse.'},
                                          'filter_tenant': {   'type': 'string',
                                                               'description': "'current' (default, "
                                                                              'aktualni tenant), '
                                                                              "'all' "
                                                                              '(cross-tenant, jen '
                                                                              'rodic), nebo '
                                                                              'substring nazvu '
                                                                              'tenantu (EUROSOFT, '
                                                                              '...).'}}},
    '_order': 44}
