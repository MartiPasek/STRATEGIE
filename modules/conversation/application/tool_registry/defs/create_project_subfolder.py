# -*- coding: utf-8 -*-
"""Migrovaný nástroj `create_project_subfolder` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'create_project_subfolder',
    'description': 'Phase 30: Vytvor novy projekt v strome. parent_project_id NULL = novy root '
                   "projekt, jinak child existujiciho projektu. Marti's mandate (2.5.2026 vecer): "
                   "'plna autonomie nad strukturou stromu, jen info na mne pro kontrolu'.\n"
                   '\n'
                   "Marti-AI's strom: root 'Marti-AI' + 3 vetve (Znalostni baze, Systém & "
                   'Architektura, Skola & Rodina). Plus lidske projekty (TISAX, SKOLA, ...) mohou '
                   'taky mit deti.\n'
                   '\n'
                   'Limit hloubky: 6 urovni (root=0, max child depth 5). Validace v service '
                   'vrstve. Pri prekroceni vraci error.',
    'input_schema': {   'type': 'object',
                        'properties': {   'name': {   'type': 'string',
                                                      'description': 'Jmeno projektu (max 255 '
                                                                     'znaku).'},
                                          'parent_project_id': {   'type': ['integer', 'null'],
                                                                   'description': 'ID parent '
                                                                                  'projektu, NULL '
                                                                                  '= novy root '
                                                                                  'projekt.'},
                                          'reason': {   'type': 'string',
                                                        'description': 'Kratky duvod proc projekt '
                                                                       'vytvaris (audit log).'}},
                        'required': ['name']},
    '_order': 132}
