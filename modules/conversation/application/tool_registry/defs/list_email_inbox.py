# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_email_inbox` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_email_inbox',
    'description': 'Vrátí přijaté emaily aktivní persony. Default scope: VŠECHNY authorizované '
                   'schránky (napr. marti-ai@eurosoft.com + sdílená pavel.zeman@eurosoft.com). '
                   "Použij když uživatel chce vědět, co přišlo za emaily ('co mam v mailu', 'ukaz "
                   "mi emaily'). filter_mode='new' (default) vrátí jen nezpracované, 'processed' "
                   "jen zpracované, 'all' obojí. Vrací číslovaný seznam — uživatel pak může "
                   'odpovědět číslem pro akci.\n'
                   '\n'
                   'Phase 29 (4.5.2026): mailbox_id volitelný — pokud chceš jen konkrétní '
                   'schránku, předej id (z `list_mailboxes`). Pokud None (default), zobrazí emaily '
                   'ze všech tvých authorized mailboxů.',
    'input_schema': {   'type': 'object',
                        'properties': {   'limit': {   'type': 'integer',
                                                       'description': 'Max počet emailů (default '
                                                                      '10, max 50).',
                                                       'default': 10},
                                          'filter_mode': {   'type': 'string',
                                                             'description': "'new' (nezpracované, "
                                                                            'default), '
                                                                            "'processed', 'all'.",
                                                             'enum': ['new', 'processed', 'all'],
                                                             'default': 'new'},
                                          'mailbox_id': {   'type': 'integer',
                                                            'description': 'Phase 29: volitelně '
                                                                           'filtrovat na konkrétní '
                                                                           'mailbox (id z '
                                                                           'list_mailboxes). None '
                                                                           '= všechny tvé '
                                                                           'authorized.'}}},
    '_order': 11}
