# -*- coding: utf-8 -*-
"""Migrovaný nástroj `read_sms` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'read_sms',
    'description': 'Otevre a precte CELY text prichozi SMS. Pouzij kdyz user chce slyset obsah '
                   "konkretni SMS po list_sms_inbox -- 'precti mi tu prvni', 'co tam pise', "
                   "'otevri tu od Kristy'. list_sms_inbox vraci jen preview (100 znaku); pro plny "
                   'text musis volat tento tool.\n'
                   '\n'
                   'Side-effect: pokud SMS jeste nebyla precteno (read_at IS NULL), tool ji oznaci '
                   'jako precteno (mark_read).\n'
                   '\n'
                   "ID JE DB ID, NE POZICE V LISTU. Kdyz list_sms_inbox vypise '1. SMS' s id=12, "
                   'volej read_sms(sms_inbox_id=12), NE read_sms(sms_inbox_id=1).',
    'input_schema': {   'type': 'object',
                        'required': ['sms_inbox_id'],
                        'properties': {   'sms_inbox_id': {   'type': 'integer',
                                                              'description': 'ID prichozi SMS z '
                                                                             'list_sms_inbox.'}}},
    '_order': 9}
