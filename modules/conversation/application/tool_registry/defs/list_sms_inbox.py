# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_sms_inbox` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_sms_inbox',
    'description': 'Vrátí přijaté SMS aktivní persony (Marti-AI vlastní firemní SIM). Použij když '
                   "uživatel chce vědět, co Marti-AI přišlo za zprávy (napr. 'co mi prislo', 'kdo "
                   "mi napsal', 'ukaz mi prichozi SMS', 'ukaz tu SMS' v kontextu daily overview).\n"
                   '\n'
                   'DEFAULT: unread_only=true -- vrátí JEN NEZPRACOVANÉ SMS (analogie '
                   "list_email_inbox kde default filter_mode='new'). Sjednocuje s "
                   'get_daily_overview, ktery taky pocita jen nezpracovane.\n'
                   '\n'
                   "Pokud user vyslovne chce VSECHNY (i zpracovane) -- napr. 'ukaz vsechny SMS', "
                   "'historie SMS', 'co jsi uz precetla' -- nastav unread_only=false. Bez tohoto "
                   'explicit pokynu nech default true, aby Marti dostal cisty seznam toho, co se '
                   'musi resit.',
    'input_schema': {   'type': 'object',
                        'properties': {   'limit': {   'type': 'integer',
                                                       'description': 'Max počet SMS (default 10, '
                                                                      'max 50).',
                                                       'default': 10},
                                          'unread_only': {   'type': 'boolean',
                                                             'description': 'Default true = jen '
                                                                            'nezpracované. False = '
                                                                            'vše (i zpracované).',
                                                             'default': True}}},
    '_order': 8}
