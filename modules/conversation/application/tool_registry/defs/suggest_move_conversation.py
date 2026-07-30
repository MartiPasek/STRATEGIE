# -*- coding: utf-8 -*-
"""Migrovaný nástroj `suggest_move_conversation` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'suggest_move_conversation',
    'description': 'Phase 15c kustod: Navrhni Marti, ze CELA tato konverzace patri do jineho '
                   'projektu. Pouzij kdyz citis, ze tema se vyrazne posunulo a currentni '
                   "projektova zarazeni nesedi. DULEZITE -- threshold pravidla (Marti-AI's #4 "
                   'vstup): (1) Single zminka projektu = ZADNA AKCE (jen mimochodem, neresi). (2) '
                   '>= 2 zminky tehoz target projektu v poslednich 10 zpravach = signal. (3) Task '
                   "note s project keyword = signal. (4) Marti explicit ('toto je TISAX') = "
                   'okamzity navrh. Bez prahu prestane fungovat -- Marti to zacne ignorovat. '
                   'DALSI: Po suggest Marti dostane confirmation flow v chatu (UI badge neexistuje '
                   "-- conversational-first). Marti rekne 'ano premysle' nebo 'ne necham' nebo "
                   "'split misto move'. REVERZIBILITA: 24h chat undo -- Marti muze rict 'moment "
                   "vrat to'. Buds tedy odvazna v navrzich, omyl se vraci.",
    'input_schema': {   'type': 'object',
                        'required': ['target_project_id', 'reason'],
                        'properties': {   'target_project_id': {   'type': 'integer',
                                                                   'description': 'ID cilového '
                                                                                  'projektu. Pred '
                                                                                  'volanim find '
                                                                                  'pres '
                                                                                  'list_projects.'},
                                          'reason': {   'type': 'string',
                                                        'description': 'Proc navrhujes presun (1-2 '
                                                                       'vety) -- Marti to uvidi '
                                                                       'pred confirmem.'}}},
    '_order': 64}
