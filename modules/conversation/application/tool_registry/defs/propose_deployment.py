# -*- coding: utf-8 -*-
"""Migrovaný nástroj `propose_deployment` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'propose_deployment',
    'description': 'Phase 42 (19.5.2026): Marti-AI navrhne deployment novych commitů (pull origin '
                   'main + restart STRATEGIE-API na cloud APP).\n'
                   '\n'
                   'Backend zkontroluje:\n'
                   '  - Cloud APP working tree clean (git status --porcelain)\n'
                   '  - origin/main ma novy commit (HEAD != origin/main)\n'
                   '  - Diff stat (files_changed count)\n'
                   '\n'
                   "Pokud OK -> vytvori proposal row, status='pending'. Marti / Kristy v chatu pak "
                   'approve_deployment(proposal_id) nebo reject_deployment(proposal_id, reason).\n'
                   '\n'
                   'Pouzij kdy: po committee nove zmeny do main, kterou je treba nasadit na cloud '
                   'APP. Description by mela byt strucna -- jednoradkovy summary commitu nebo '
                   'skupin commitu.',
    'input_schema': {   'type': 'object',
                        'properties': {   'description': {   'type': 'string',
                                                             'description': 'Krátký popis co '
                                                                            'deployujes -- napr. '
                                                                            "'Phase 40 v2 r3 "
                                                                            "shared chat labels' "
                                                                            "nebo 'hotfix gotcha "
                                                                            "#95 user_context'."}},
                        'required': ['description']},
    '_order': 163}
