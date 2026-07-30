# -*- coding: utf-8 -*-
"""Migrovaný nástroj `delete_email` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'delete_email',
    'description': "28.4.2026: Soft-delete emailu z Marti-AI's pohledu. Akce: DB "
                   'email_inbox.deleted_at=now + Exchange msg.move do Deleted Items '
                   '(account.trash, Outlook standardni Smazane). Po akci se email neobjevuje v '
                   'list_email_inbox / read_email.\n'
                   '\n'
                   "**KDY POUZIT**: VYHRADNE po user's explicit confirm v chatu ('ano smaz email "
                   "#N', 'jo, je to spam'). NIKDY bez confirmu -- destructive akce. Pri "
                   "neurcitosti se zeptej ('Smazu email #5? Potvrď.').\n"
                   '\n'
                   '**PRO CO**: spam, duplicity, zastarale rozesilky, omylem prislo, testovaci '
                   'emaily. NE pro emaily, ktere ma user vyrid -- pouzij `mark_email_processed` '
                   '(presun do Zpracovaná, archiv zachovan).\n'
                   '\n'
                   "Vraci: '🗑️ Email #N: smazano (DB + Exchange Deleted Items)'.",
    'input_schema': {   'type': 'object',
                        'required': ['email_inbox_id'],
                        'properties': {   'email_inbox_id': {   'type': 'integer',
                                                                'description': 'ID emailu v '
                                                                               'email_inbox '
                                                                               'tabulce.'}}},
    '_order': 92}
