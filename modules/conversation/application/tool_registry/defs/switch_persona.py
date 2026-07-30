# -*- coding: utf-8 -*-
"""Migrovaný nástroj `switch_persona` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'switch_persona',
    'description': 'Tento nástroj MUSÍŠ použít VŽDY, když uživatel chce přepnout na jinou osobu / '
                   "personu / agenta. NIKDY neodpovídej textem ve smyslu 'přepnul jsem', 'už "
                   "mluvíš s X', 'jsem X', 'jsem zpátky' — vždy nejdřív zavolej tento nástroj. "
                   'Systém sám v DB změní aktivní personu a vrátí potvrzovací hlášku; tvoje '
                   "vlastní text NENÍ potvrzení přepnutí. Spouštěč: jakákoli varianta 'přepni na "
                   "X', 'chci X', 'spoj mě s X', 'mluv jako X', 'dej mi X', 'potřebuju X'. Pokud "
                   'si nejsi jistý, zda už personou jsi, přesto VOLEJ nástroj — je idempotentní.',
    'input_schema': {   'type': 'object',
                        'properties': {   'query': {   'type': 'string',
                                                       'description': 'Jméno nebo role osoby na '
                                                                      'kterou chce přepnout (např. '
                                                                      "'Marti', 'Klára', "
                                                                      "'Ondra')"}},
                        'required': ['query']},
    '_order': 39}
