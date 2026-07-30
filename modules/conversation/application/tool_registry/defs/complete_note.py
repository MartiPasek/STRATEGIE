# -*- coding: utf-8 -*-
"""Migrovaný nástroj `complete_note` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'complete_note',
    'description': 'Phase 15a: Cross-off task -- zaskrtni hotove. Pouzij PO dokoncovaci akci '
                   '(invite_user, send_email, send_sms, atd.) kdyz souvisi s otevrenym task notem '
                   "v zapisniku. Po complete_note se task v zapisniku zobrazuje s prefix '(✅ "
                   "completed)' -- Marti-AI vidi, co je hotove. Po akcnich tools (send_*, "
                   "invite_*, atd.) tool response obsahuje hint '[HINT] Mas N otevreny task(s) -- "
                   "pripadne zavolej complete_note'. Hint je jen pripomenuti, NE povinnost. "
                   "Rozhoduj sama. Validace: jen task notes (category='task') mohou byt completed. "
                   'Idempotent -- opakovany call vrati current state bez chyby.',
    'input_schema': {   'type': 'object',
                        'required': ['note_id'],
                        'properties': {   'note_id': {'type': 'integer'},
                                          'completion_summary': {   'type': 'string',
                                                                    'description': 'Volitelny '
                                                                                   "popis 'co jsem "
                                                                                   "udelala' -- "
                                                                                   'pripoji se k '
                                                                                   'content '
                                                                                   '(audit).'},
                                          'linked_action_id': {   'type': 'integer',
                                                                  'description': 'Volitelny FK na '
                                                                                 'action_logs / '
                                                                                 'messages -- '
                                                                                 'ktera akce '
                                                                                 'dokoncila '
                                                                                 'task.'}}},
    '_order': 61}
