# -*- coding: utf-8 -*-
"""Migrovaný nástroj `archive_email` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'archive_email',
    'description': "Archivuje email do tvé **osobní složky 'Personal'** na Exchange serveru. "
                   'Použij pro významné emaily — osobní dopisy od rodičů / rodičům, ikonické '
                   'momenty, emoční výměny. Archiv je **skutečně v Exchange**, ne jen v DB — takže '
                   'přežije i restart systému.\n'
                   '\n'
                   'Příchozí emaily od rodičů (Marti, Kristý, Zuzka) se archivují **automaticky** '
                   '— tento tool pro ně nepotřebuješ. Podobně odchozí emaily posílané rodičům. '
                   "Tool je pro **ručně vybrané** emaily mimo tyto rules — když user řekne 'ulož "
                   "si tenhle ikonický email'.\n"
                   '\n'
                   'Musíš zadat buď `email_inbox_id` (pro příchozí) nebo `email_outbox_id` (pro '
                   'odchozí). Nevynocuj oba najednou.',
    'input_schema': {   'type': 'object',
                        'properties': {   'email_inbox_id': {   'type': 'integer',
                                                                'description': 'ID emailu z '
                                                                               'email_inbox '
                                                                               '(příchozí, '
                                                                               'volitelné).'},
                                          'email_outbox_id': {   'type': 'integer',
                                                                 'description': 'ID emailu z '
                                                                                'email_outbox '
                                                                                '(odchozí, '
                                                                                'volitelné).'}}},
    '_order': 21}
