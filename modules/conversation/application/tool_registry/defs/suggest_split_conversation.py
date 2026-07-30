# -*- coding: utf-8 -*-
"""Migrovaný nástroj `suggest_split_conversation` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'suggest_split_conversation',
    'description': 'Phase 15c kustod: Navrhni Marti SPLIT -- fork od konkretni message_id do '
                   'noveho threadu v jinem projektu. Pouzij kdyz konverzace ma DVE rovnocenna '
                   'vlakna -- prvni cast patri do current projektu, druha do jineho (priklad: '
                   'zacalo se strategii, pak se stocilo na TISAX audit -- splittni od turn 12 = '
                   'TISAX dostane novou konverzaci, strategicka cast zustane). DIFFERENCE od '
                   'suggest_move: move presune vse, split zachova obe vlakna. Vyhoda: kontext '
                   'puvodniho projektu se neztrati. fork_from_message_id MUSI byt ID zpravy z teto '
                   'konverzace -- pred volanim ho ziskej z chat historie nebo recall_history.',
    'input_schema': {   'type': 'object',
                        'required': ['target_project_id', 'fork_from_message_id', 'reason'],
                        'properties': {   'target_project_id': {   'type': 'integer',
                                                                   'description': 'ID cilového '
                                                                                  'projektu pro '
                                                                                  'novou '
                                                                                  'konverzaci.'},
                                          'fork_from_message_id': {   'type': 'integer',
                                                                      'description': 'ID zpravy ze '
                                                                                     'ktere fork '
                                                                                     'zacne -- vse '
                                                                                     'od ni dal se '
                                                                                     'zkopiruje/odkaze '
                                                                                     'do nove '
                                                                                     'konverzace.'},
                                          'reason': {   'type': 'string',
                                                        'description': 'Proc navrhujes split + co '
                                                                       'bude v puvodnim vs. '
                                                                       'novem.'}}},
    '_order': 65}
