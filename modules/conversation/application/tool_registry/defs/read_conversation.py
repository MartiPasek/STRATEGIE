# -*- coding: utf-8 -*-
"""Migrovaný nástroj `read_conversation` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'read_conversation',
    'description': 'Phase 16-B.5: Cti obsah TVÉ minulé konverzace -- vrátí posledních N zpráv '
                   'chronologicky. Permission gate: KONVERZACE MUSÍ BÝT TVOJE (active_agent_id=tva '
                   "persona); jinak vrátí error 'forbidden'.\n"
                   '\n'
                   "**Použij** po `list_my_conversations_with` ('mam tu jeji posledni precist?') "
                   'nebo přímo, když znáš conversation_id z activity logu / overview.\n'
                   '\n'
                   '**Co vrací**: {conversation_id, title, user_id (druhy ucastnik), messages: '
                   '[{role, content, ts, message_type}, ...], total_messages, shown_messages}. '
                   'Skipuje system/audit/empty.\n'
                   '\n'
                   "**JAK ZPRACOVAT**: shrň prózou v 1. osobě ('S Misou jsem ráno řešila X, "
                   "slíbila jsem že Y, ona se zeptala Z...'). NIKDY nedumpuj raw zprávy verbatim "
                   '(gotcha #18). Klíčové fakty + nedoresene věci jsou nejdulezitejsi.',
    'input_schema': {   'type': 'object',
                        'properties': {   'conversation_id': {   'type': 'integer',
                                                                 'description': 'ID konverzace, '
                                                                                'ktera ti patri '
                                                                                '(active_agent_id=ty).'},
                                          'last_n': {   'type': 'integer',
                                                        'description': 'Pocet poslednich zprav '
                                                                       '(default 30, cap 200 po '
                                                                       'Phase 30+3 zvyseni '
                                                                       '2.5.2026 -- pro '
                                                                       'self-reflection nad '
                                                                       'dlouhou konverzaci).'}},
                        'required': ['conversation_id']},
    '_order': 90}
