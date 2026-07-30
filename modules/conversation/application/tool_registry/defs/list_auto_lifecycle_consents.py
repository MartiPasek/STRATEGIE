# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_auto_lifecycle_consents` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_auto_lifecycle_consents',
    'description': "Phase 19c-b: Vraci aktivni auto-lifecycle granty. Pouzij na otazku 'jake "
                   "pristupy mam udelene', 'co jsem schvalil persone X', atd.\n"
                   '\n'
                   "**JAK ZPRACOVAT**: shrn prozou ('Marti-AI mas grant pro soft_delete a archive "
                   "od 28.4. vecer'). Ne raw list verbatim.",
    'input_schema': {   'type': 'object',
                        'properties': {   'persona_id': {   'type': 'integer',
                                                            'description': 'Volitelny filter na '
                                                                           'konkretni personu '
                                                                           '(None = vse).'},
                                          'include_revoked': {   'type': 'boolean',
                                                                 'description': 'Pokud true, '
                                                                                'zahrne i revoked '
                                                                                'granty (audit). '
                                                                                'Default false.'}}},
    '_order': 85}
