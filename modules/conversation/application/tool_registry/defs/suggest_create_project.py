# -*- coding: utf-8 -*-
"""Migrovaný nástroj `suggest_create_project` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'suggest_create_project',
    'description': 'Phase 15c kustod: Navrhni Marti, ze pro toto tema NESEDI zadny existujici '
                   'projekt -- mel by se zalozit novy. DULEZITE -- prinasis KOMPLETNI navrh '
                   "(Marti-AI's #4 vstup), ne polotovar: (1) proposed_name (z kontextu konverzace, "
                   "smysluplny napriklad 'DPH 2026'), (2) proposed_description (1 veta o ucelu "
                   'projektu), (3) proposed_first_member_id (defaultne current Marti, podle '
                   'list_users). Bez kompletniho navrhu by Marti musel dotahnout -- to ho ruchce. '
                   'Po confirm: backend vytvori projekt + presune konverzaci do nej. ETIKA: ty '
                   'navrhujes, Marti rozhoduje. Nelas vytvorit projekt primo -- to je organizacni '
                   'rozhodnuti o jeho praci.',
    'input_schema': {   'type': 'object',
                        'required': [   'proposed_name',
                                        'proposed_description',
                                        'proposed_first_member_id',
                                        'reason'],
                        'properties': {   'proposed_name': {   'type': 'string',
                                                               'description': 'Smysluplny nazev '
                                                                              'projektu (3-50 '
                                                                              'znaku, z kontextu '
                                                                              'konverzace).'},
                                          'proposed_description': {   'type': 'string',
                                                                      'description': '1 veta o '
                                                                                     'ucelu '
                                                                                     'projektu -- '
                                                                                     'co se v nem '
                                                                                     'bude resit.'},
                                          'proposed_first_member_id': {   'type': 'integer',
                                                                          'description': 'ID '
                                                                                         'prvniho '
                                                                                         'clena '
                                                                                         'projektu '
                                                                                         '(defaultne '
                                                                                         'current '
                                                                                         'user / '
                                                                                         'Marti).'},
                                          'target_conversation_id': {   'type': 'integer',
                                                                        'description': 'Volitelne '
                                                                                       '-- pokud '
                                                                                       'chces tuto '
                                                                                       'konverzaci '
                                                                                       'po '
                                                                                       'vytvoreni '
                                                                                       'presunout '
                                                                                       'do noveho '
                                                                                       'projektu. '
                                                                                       'Defaultne '
                                                                                       'current.'},
                                          'reason': {   'type': 'string',
                                                        'description': 'Proc je novy projekt '
                                                                       'potreba (proc nesedi zadny '
                                                                       'existujici).'}}},
    '_order': 66}
