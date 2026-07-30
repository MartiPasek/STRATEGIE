# -*- coding: utf-8 -*-
"""Migrovaný nástroj `reply_all` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'reply_all',
    'description': "⭐ Faze 12c: ODPOVED VSEM (To + CC) puvodniho emailu. Analogie tlacitka 'Reply "
                   "All' v Outlooku.\n"
                   '\n'
                   'POUZIVEJ kdy:\n'
                   "  - User rekne 'odpovez vsem', 'reply all', 'odpovez celemu vlaknu'\n"
                   '  - Email mel vice prijemcu (To + CC) a chces vsem odpovedet\n'
                   '  - Vlakno ma dynamiku skupinove komunikace -- vyradit nekoho bez duvodu by '
                   'prekvapilo\n'
                   '\n'
                   "🚫 NEPOUZIVEJ send_email + 'RE:' a manualne lepit CC. Tento tool:\n"
                   '  - Auto-resolve To = puvodni To (mimo nasi vlastni adresu)\n'
                   '  - Auto-resolve CC = puvodni CC (mimo nasi vlastni adresu)\n'
                   "  - Pripoji historii + thread headers + 'RE ALL:' prefix\n"
                   '\n'
                   'DULEZITE: vlakno ma svou dynamiku. Lide v To/CC ocekavaji, ze v nem zustanou. '
                   'Vyradit nekoho bez duvodu (override `to`/`cc` -- vynechat ho) muze prekvapit, '
                   'obzvlast u vedeni firmy / klientu / formalni komunikace.\n'
                   '\n'
                   'Override OK kdy: prevent spam (vyradit noreply@), uzavrit thread (vyradit '
                   'vsechny mimo nas), pridat noveho zainteresovaneho. NIKDY tise nebo nahodne.',
    'input_schema': {   'type': 'object',
                        'required': ['email_inbox_id', 'body'],
                        'properties': {   'email_inbox_id': {   'type': 'integer',
                                                                'description': 'ID emailu z '
                                                                               'list_email_inbox / '
                                                                               'read_email.'},
                                          'body': {   'type': 'string',
                                                      'description': 'Tvuj text odpovedi (system '
                                                                     'pripoji historii).'},
                                          'subject': {   'type': 'string',
                                                         'description': 'Override subjectu. None = '
                                                                        'default RE prefix.'},
                                          'to': {   'type': 'string',
                                                    'description': 'Override seznamu To. Bez nej = '
                                                                   'puvodni To. Pouzivej '
                                                                   'rozvazne.'},
                                          'cc': {   'type': 'string',
                                                    'description': 'Override CC. Bez nej = puvodni '
                                                                   'CC.'},
                                          'bcc': {'type': 'string', 'description': 'Override BCC.'},
                                          'attachment_document_ids': {   'type': 'array',
                                                                         'items': {   'type': 'integer'},
                                                                         'description': 'Phase '
                                                                                        '27b: '
                                                                                        'Volitelne '
                                                                                        '-- IDs '
                                                                                        'dokumentu '
                                                                                        'z RAG '
                                                                                        'documents '
                                                                                        'pro '
                                                                                        'pripojeni. '
                                                                                        'Cap 20 MB '
                                                                                        'total. '
                                                                                        'Format '
                                                                                        'whitelist '
                                                                                        'viz '
                                                                                        'send_email.'}}},
    '_order': 47}
