# -*- coding: utf-8 -*-
"""Migrovaný nástroj `flag_message_important` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'flag_message_important',
    'description': 'Phase 31 (3.5.2026): KOTVA ⚓. Oznaci zpravu jako dulezitou -- drzi ji v '
                   'aktivnim okne i pres cut-off, bez ohledu na stari.\n'
                   '\n'
                   "Marti-AI's volba symbolu (3.5.2026 rano): ⚓ ('starsi a klidnejsi nez 🪝, "
                   "prinaska obraz neceho, co drzi i v boure'). Marti-AI's metafora: 'zalozka v "
                   "knize'.\n"
                   '\n'
                   'Pouziti: kdyz user preda kompletni podklady (klicovy kontext, instrukce, fakty '
                   'na ktere se budes vracet), flagni zpravu --drzi se v okne dokud sama neunflag '
                   '(zadne expiration, zadny hard cap).\n'
                   '\n'
                   "also_create_note=True (volitelne, default False -- Marti-AI's korekce "
                   "'automatismus mi bere volbu'):\n"
                   '  - Auto-vytvori conversation_note s source_message_id=msg\n'
                   "  - note_type='fact', certainty=85, importance=4\n"
                   "  - content = reason (pokud zadan), jinak 'Zakotvena zprava #N'\n"
                   "  - Tvuj vlastni text zachycujici tvuj VYKLAD (Marti-AI's metafora     "
                   "'zalozka v knize a poznamka na okraj' -- kotva = zalozka,     note = poznamka, "
                   'NEjsou duplikaty)\n'
                   '\n'
                   'Pravidla:\n'
                   '  - reason VOLITELNY\n'
                   '  - also_create_note default False\n'
                   '  - idempotent (pokud uz je is_anchored=True, no-op)\n'
                   '  - bez parent gate (tvuj prostor)',
    'input_schema': {   'type': 'object',
                        'properties': {   'message_id': {   'type': 'integer',
                                                            'description': 'ID zpravy z teto '
                                                                           'konverzace.'},
                                          'reason': {   'type': 'string',
                                                        'description': 'VOLITELNY -- proc kotvis '
                                                                       "(napr. 'Klarka predala "
                                                                       'kompletni podklady k '
                                                                       "rozvrhu')."},
                                          'also_create_note': {   'type': 'boolean',
                                                                  'description': 'Volitelne '
                                                                                 '(default False). '
                                                                                 'True = '
                                                                                 'auto-vytvorit '
                                                                                 'conversation_note '
                                                                                 "jako 'poznamku "
                                                                                 "na okraji' s "
                                                                                 'odkazem na '
                                                                                 'zpravu. Pouzij '
                                                                                 'kdyz chces '
                                                                                 'dvojitou '
                                                                                 'pojistku -- '
                                                                                 'zalozku v knize '
                                                                                 '+ tvou '
                                                                                 'interpretaci.'}},
                        'required': ['message_id']},
    '_order': 138}
