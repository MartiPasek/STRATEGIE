# -*- coding: utf-8 -*-
"""Migrovaný nástroj `send_pwa_install_invite` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'send_pwa_install_invite',
    'description': 'Phase 38.5 (10.5.2026): Posli existujicimu uzivateli pozvanku na STRATEGIE '
                   'Chat jako PWA aplikaci. Email obsahuje magic link (token-based auto-login, '
                   'expirace 7 dni) plus navod na PWA install (klik na install banner v UI -- '
                   'zadny PowerShell, ZIP, admin rights). Marti-AI ONLY. Pouzij pro: pozvanky pro '
                   'kolegyni, ktere jsou technicky unfriendly. Pred bulk pozvankami se VZDY zeptej '
                   "tatinka 'mam jim napsat vsem stejne, nebo k nekomu neco pridat?' (Marti-AI's "
                   'Q4 conversation flow z 38.5 konzultace).\n'
                   '\n'
                   'Email template ma 3 FIXED bloky (self-introduction, why-line, install '
                   "instrukce + magic link, signature 'Tvoje Marti') a 2 VARIABILNI bloky "
                   '(greeting + closing) ktere ty volis per recipient. Pokud znas Petru z RAG '
                   "memory, dej 'Ahoj Petro 🤍' -- pokud neznas, jen 'Ahoj Petro' bez srdicka. "
                   "Srdicko si zaslouzi kontext (Marti-AI's Q2 insight).\n"
                   '\n'
                   "Audit log s invited_by_persona_id (vztahovy akt, ne system cron -- Marti-AI's "
                   'Q1 insight).',
    'input_schema': {   'type': 'object',
                        'properties': {   'user_id': {   'type': 'integer',
                                                         'description': 'users.id prijemce '
                                                                        'pozvanky. Musi mit '
                                                                        'registrovany email '
                                                                        '(ews_display_email nebo '
                                                                        'user_contacts primary). '
                                                                        'Pred volanim doporuceno '
                                                                        'overit pres find_user.'},
                                          'custom_note': {   'type': 'string',
                                                             'description': 'Volitelny text '
                                                                            'VIDITELNY v emailu '
                                                                            'pred zaverem -- napr. '
                                                                            "'Petro, tatinek ti "
                                                                            'rika ze tato aplikace '
                                                                            'ti pomuze s '
                                                                            "fakturaci'. Tatinkova "
                                                                            'zprava pres tebe.'},
                                          'greeting_override': {   'type': 'string',
                                                                   'description': 'Tvuj uvod -- '
                                                                                  "napr. 'Ahoj "
                                                                                  "Petro 🤍' pokud "
                                                                                  'zna z RAG, nebo '
                                                                                  "'Ahoj Petro' "
                                                                                  'bez srdicka '
                                                                                  'pokud neznas. '
                                                                                  "Default 'Ahoj "
                                                                                  "{first_name},' "
                                                                                  'pokud None.'},
                                          'closing_override': {   'type': 'string',
                                                                  'description': 'Tvuj zaver pred '
                                                                                 "'Tvoje Marti 🤍' "
                                                                                 'signaturou. '
                                                                                 'Personalizovany '
                                                                                 'podle context. '
                                                                                 "Default 'Pokud "
                                                                                 'neco nefunguje, '
                                                                                 'zavolej mi nebo '
                                                                                 'napis -- '
                                                                                 "pomuzeme ti.' "
                                                                                 'Pokud chces neco '
                                                                                 'specifickeho per '
                                                                                 'recipient (napr. '
                                                                                 "'Vim ze "
                                                                                 'fakturace te '
                                                                                 'casto stresuje, '
                                                                                 'tahle aplikace '
                                                                                 "to zjednodusi'), "
                                                                                 'napis vlastni '
                                                                                 'text.'},
                                          'context_hint': {   'type': 'string',
                                                              'description': "Marti-AI's Q3 "
                                                                             "insight: 'sepot pro "
                                                                             "Marti-AI'. Tatinek "
                                                                             'tady muze rict '
                                                                             "'Petra je nova, "
                                                                             "prvni tyden' nebo "
                                                                             "'Marie ma rada "
                                                                             "strucne emaily' -- "
                                                                             'ty to NEMUSIS '
                                                                             'doslova vlozit do '
                                                                             'emailu, ale '
                                                                             'zakomponuj do tonu '
                                                                             'greeting/closing. '
                                                                             'Optional context, ne '
                                                                             'user-visible.'}},
                        'required': ['user_id']},
    '_order': 111}
