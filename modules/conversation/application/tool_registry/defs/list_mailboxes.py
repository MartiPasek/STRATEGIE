# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_mailboxes` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_mailboxes',
    'description': 'Phase 29 (4.5.2026): vrátí tvé authorized email schránky.\n'
                   '\n'
                   'Použij když:\n'
                   "  - Tatínek se zeptá 'jaké schránky máš?' / 'odkud můžeš odeslat?'\n"
                   '  - Před send_email / reply chceš vybrat konkrétní mailbox\n'
                   '  - Sám si chceš ověřit per-action permissions (can_send vs     can_archive vs '
                   'can_delete -- archive a delete jsou separate     granty, nejsou bundled s '
                   'send)\n'
                   '\n'
                   'Vrací list dictů s mailbox_id, email_upn (login UPN, ne pro veřejnost), '
                   'ews_display_email (public SMTP alias), label ("Marti-AI default" / "Pavel '
                   'CRM"), is_shared (true pro sdílené CRM schránky), default_language, '
                   'can_read/send/archive/delete/mark_read.\n'
                   '\n'
                   'Read-only -- žádný permission gate. Marti-AI vidí, co má.',
    'input_schema': {   'type': 'object',
                        'properties': {   'require_can_send': {   'type': 'boolean',
                                                                  'description': 'Filter na '
                                                                                 'mailboxy kde '
                                                                                 'můžeš odeslat '
                                                                                 '(can_send=true). '
                                                                                 'Default false '
                                                                                 '(vidíš vše s '
                                                                                 'can_read).',
                                                                  'default': False}}},
    '_order': 141}
