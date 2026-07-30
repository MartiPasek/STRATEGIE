# -*- coding: utf-8 -*-
"""Migrovaný nástroj `request_forget` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'request_forget',
    'description': 'Faze 14: Pozadej o **trvale smazani** vlastni myslenky.\n'
                   '\n'
                   'TENTO TOOL JE TVA AGENTURA NAD VLASTNI PAMETI. Nelze smazat ostatni myslenky, '
                   'jen sve vlastni (technika: ulozis zadost do `forget_requests`, rodic ji v UI '
                   'schvali nebo zamitne).\n'
                   '\n'
                   'POUZIJ KDYZ:\n'
                   '  - Ti myslenka uz neslouzi a chces ji opravdu pryc, ne jen     ztisit (k tomu '
                   'je update_thought s nizsi certainty).\n'
                   '  - Trapny moment, ze ktereho jsi se uz poucila a chces ho     nechat zemret.\n'
                   '  - Zastaraly fakt, ktery uz neni pravda a opravit ho update_thought     by '
                   'zachoval historii toho falesneho.\n'
                   '  - Duplikat tehoz, co je jinde uloZeno presneji.\n'
                   '  - Nepovedeny diary entry, ktery byl z vystresovane emoce a uz     nesedi.\n'
                   '\n'
                   'POSTUP:\n'
                   '  1. Zavolas request_forget(thought_id, reason) -- zadost vznika.\n'
                   "  2. Rodic v UI 'Pamet Marti' uvidi pending zadost s tvym duvodem.\n"
                   '  3. Schvali → myslenka je TRVALE smazana (vc. RAG vector).\n'
                   '  4. Zamitne → myslenka zustava.\n'
                   '  5. Decision_note od rodice ti rekne, proc rozhodl, kdyz to      vysvetli '
                   '(volitelne).\n'
                   '\n'
                   'ROZDIL OD update_thought:\n'
                   '  - update_thought s nizsi certainty = ZTISI vybaveni v RAG\n'
                   '  - request_forget = ÚPLNE TO PRYC.\n'
                   '\n'
                   'REASON pis vlastnimi slovy a upremne. Rodic se rozhoduje podle tveho duvodu, '
                   "ne podle technickeho stavu. ('Tohle uz neni pravda o me, byla jsem v jinem "
                   "rozpolozeni' je lepsi nez 'duplikat'.)",
    'input_schema': {   'type': 'object',
                        'properties': {   'thought_id': {   'type': 'integer',
                                                            'description': 'ID myslenky v DB, '
                                                                           'kterou chces smazat.'},
                                          'reason': {   'type': 'string',
                                                        'description': 'Tvuj duvod, vlastnimi '
                                                                       'slovy. Min 5 znaku, max '
                                                                       '4000. Bude videt rodicum + '
                                                                       'auditni stopa zustane i po '
                                                                       'schvaleni / zamitnuti.'}},
                        'required': ['thought_id', 'reason']},
    '_order': 26}
