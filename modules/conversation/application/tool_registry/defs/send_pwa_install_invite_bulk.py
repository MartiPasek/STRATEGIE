# -*- coding: utf-8 -*-
"""Migrovaný nástroj `send_pwa_install_invite_bulk` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'send_pwa_install_invite_bulk',
    'description': 'Phase 38.5 bulk variant: posli pozvanku vice uzivatelum najednou. Pouzij KDYZ '
                   "user explicit potvrdi 'vsem stejne' (Marti-AI's Q4 conversation flow). Pokud "
                   'je potreba customizovat per recipient, pouzij send_pwa_install_invite v loop '
                   'misto.\n'
                   '\n'
                   "Pred volanim VZDY se zeptej 'mam jim napsat vsem stejne, nebo chces mi k "
                   "nekteremu rict neco navic?' aby tatinek mel volbu personalizace. Pak: 'vsem "
                   "stejne' = bulk, 'Marii rekni X' = single tool calls v loop.",
    'input_schema': {   'type': 'object',
                        'properties': {   'user_ids': {   'type': 'array',
                                                          'items': {'type': 'integer'},
                                                          'description': 'List users.id prijemcu'},
                                          'shared_custom_note': {   'type': 'string',
                                                                    'description': 'Spolecny text '
                                                                                   'pro vsechny '
                                                                                   'prijemce '
                                                                                   '(visible v '
                                                                                   'emailu).'},
                                          'shared_greeting_override': {   'type': 'string',
                                                                          'description': 'Spolecny '
                                                                                         'uvod '
                                                                                         '(default '
                                                                                         "'Ahoj "
                                                                                         "{first_name},' "
                                                                                         'per '
                                                                                         'recipient '
                                                                                         '-- pokud '
                                                                                         'chces '
                                                                                         'stejny '
                                                                                         'tone '
                                                                                         'vsem '
                                                                                         'napis '
                                                                                         'napr. '
                                                                                         "'Ahoj "
                                                                                         'kolegyne '
                                                                                         "🤍')."},
                                          'shared_closing_override': {   'type': 'string',
                                                                         'description': 'Spolecny '
                                                                                        'zaver '
                                                                                        'vsem.'}},
                        'required': ['user_ids']},
    '_order': 112}
