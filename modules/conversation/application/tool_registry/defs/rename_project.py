# -*- coding: utf-8 -*-
"""Migrovaný nástroj `rename_project` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'rename_project',
    'description': 'Phase 30: Prejmenuj projekt. Nezmeni jeho misto v stromu, jen name field. '
                   "Existing IDs/relace zustanou. Pouzij pri zpresneni labelu (napr. 'Smlouvy' -> "
                   "'Smlouvy & pravni').",
    'input_schema': {   'type': 'object',
                        'properties': {   'project_id': {   'type': 'integer',
                                                            'description': 'ID prejmenovavaneho '
                                                                           'projektu.'},
                                          'new_name': {   'type': 'string',
                                                          'description': 'Novy nazev (max 255 '
                                                                         'znaku).'},
                                          'reason': {   'type': 'string',
                                                        'description': 'Kratky duvod prejmenovani '
                                                                       '(audit log).'}},
                        'required': ['project_id', 'new_name']},
    '_order': 135}
