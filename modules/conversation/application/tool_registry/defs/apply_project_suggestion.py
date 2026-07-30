# -*- coding: utf-8 -*-
"""Migrovaný nástroj `apply_project_suggestion` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'apply_project_suggestion',
    'description': "Phase 15c+15d: Aplikuj project zmenu PO Marti's confirm v chatu. Pouzij kdyz "
                   "Marti rekl 'ano premisle' / 'ano splittni' / 'ano zaloz projekt' na tvuj "
                   'predchozi suggest_move/split/create_project navrh. Backend si ze '
                   'suggested_project_reason rozparsuje mode (move/split/create_project) a provede '
                   'skutecnou zmenu (apply_project_change nebo fork_conversation nebo '
                   'create_project + apply). Po uspechu se suggested_project_* fields vyclear.',
    'input_schema': {   'type': 'object',
                        'properties': {   'confirm_reason': {   'type': 'string',
                                                                'description': 'Volitelny '
                                                                               'zaznamovaci '
                                                                               'komentar (napr. '
                                                                               "'Marti potvrdil v "
                                                                               "chatu')."}}},
    '_order': 69}
