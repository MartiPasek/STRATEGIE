# -*- coding: utf-8 -*-
"""Migrovaný nástroj `revoke_auto_send` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'revoke_auto_send',
    'description': 'Odvolá dříve udělený souhlas s auto-sendem. Budoucí send_email / send_sms na '
                   'daného příjemce už bude znovu vyžadovat potvrzení.\n'
                   '\n'
                   '**Oprávnění:** Pouze rodič může odvolávat. Každý z rodičů (Marti, Kristý) může '
                   'odvolat jakýkoli souhlas — kolektivní veto. Backend tě zastaví, pokud volající '
                   'není rodič.\n'
                   '\n'
                   'Identifikace: BUĎ `consent_id` (z UI), NEBO kombinace `target_user_id` + '
                   '`channel`, NEBO `target_contact` + `channel`, NEBO `target_domain` + `channel` '
                   '(Phase 27i 2.5.2026).\n'
                   '\n'
                   'Odvolání NEZMAZE historii — zůstává v auditu (kdo, kdy, proč odvolal). Znovu '
                   'povolit lze kdykoli novým `grant_auto_send`.\n'
                   '\n'
                   "Spouštěče: 'odvolej souhlas pro X', 'zruš oprávnění X', 'už X nic automaticky "
                   "neposílej', 'zruš whitelist pro doménu Y'.",
    'input_schema': {   'type': 'object',
                        'properties': {   'consent_id': {   'type': 'integer',
                                                            'description': 'ID konkrétního consent '
                                                                           'záznamu (pokud víš '
                                                                           'přesně).'},
                                          'channel': {   'type': 'string',
                                                         'enum': ['email', 'sms'],
                                                         'description': 'Který kanál odvolat '
                                                                        '(vyžadováno, pokud '
                                                                        'nezadáváš consent_id).'},
                                          'target_user_id': {   'type': 'integer',
                                                                'description': 'ID uživatele, '
                                                                               'kterému odvoláváš '
                                                                               'auto-send.'},
                                          'target_contact': {   'type': 'string',
                                                                'description': 'Email / telefon '
                                                                               'externího '
                                                                               'kontaktu.'},
                                          'target_domain': {   'type': 'string',
                                                               'description': 'Phase 27i: doména k '
                                                                              'odvolání (např. '
                                                                              "'eurosoft.com'). "
                                                                              'Jen pro '
                                                                              "channel='email'."}}},
    '_order': 42}
