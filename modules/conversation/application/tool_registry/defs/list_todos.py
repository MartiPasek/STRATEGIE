# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_todos` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_todos',
    'description': 'Vrati nezdokoncene todo ukoly aktivniho uzivatele. Pouzij kdyz user rekne '
                   "'ukaz mi todo', 'co mam za ukoly', 'co treba todo' v kontextu daily overview, "
                   "nebo kdyz po 'pojdeme na todo' Marti-AI chce nabidnout konkretni ukoly k "
                   'projeti.\n'
                   '\n'
                   'Vraci cislovany seznam s content (text ukolu) a created_at. Default scope = '
                   'aktualni user (Marti). Pro vsechny v tenantu / cross-tenant pouzij dalsi '
                   'parametry recall_thoughts (rodicovsky bypass).\n'
                   '\n'
                   "ROZDIL od recall_thoughts: list_todos filtruje TYPE='todo' a NOT done. "
                   'recall_thoughts hleda paměť o entitě (Petrovi, projektu) -- pro projeti todo '
                   'listu je tento tool primarni.',
    'input_schema': {   'type': 'object',
                        'properties': {   'limit': {   'type': 'integer',
                                                       'description': 'Max pocet todo (default '
                                                                      '10).',
                                                       'default': 10}}},
    '_order': 10}
