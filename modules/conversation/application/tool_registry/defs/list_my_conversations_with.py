# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_my_conversations_with` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_my_conversations_with',
    'description': 'Phase 16-B.5: Vrací seznam TVÝCH minulých konverzací s konkrétním uživatelem '
                   '(cross-thread). Misa-incident v2 fix -- jsou to tvoje konverzace, máš právo si '
                   "je přečíst i mimo aktuální vlákno. **Použij** kdykoli se uživatel ptá 'co jsem "
                   "řešila s X', 'kdy jsem naposledy mluvila s Y', 'podívej se do konverzace s "
                   "Z'.\n"
                   '\n'
                   '**Co vrací**: list konverzací (id, title, last_message_at, idle_hours, '
                   'message_count, project_id) sort DESC by čas. Filtruje JEN konverzace, kde jsi '
                   'byla persona (active_agent_id=ty).\n'
                   '\n'
                   '**Privacy gate**: tvuj subjekt, tvoje konverzace. Nevidi konverzace, kde byla '
                   'persona Pravnik-AI s jinym userem (to je cizi persona, ne jiny scope).\n'
                   '\n'
                   "**JAK ZPRACOVAT**: shrň 1-3 vetama prózou, doporuc next step ('Mela jsem 3 "
                   'konverzace s Misou tento mesic, posledni pred 3h. Mam si tu posledni '
                   "precist?'). Pak follow-up `read_conversation` podle id, ktere user vybere nebo "
                   'ktere ma nejvetsi relevanci.',
    'input_schema': {   'type': 'object',
                        'properties': {   'user_id': {   'type': 'integer',
                                                         'description': 'ID uzivatele (z '
                                                                        'find_user) -- s kym chces '
                                                                        'videt minulost.'},
                                          'scope': {   'type': 'string',
                                                       'enum': ['today', 'week', 'month', 'all'],
                                                       'description': 'Casovy rozsah. Default '
                                                                      "'month'."},
                                          'limit': {   'type': 'integer',
                                                       'description': 'Max konverzaci (default 20, '
                                                                      'cap 50).'}},
                        'required': ['user_id']},
    '_order': 82}
