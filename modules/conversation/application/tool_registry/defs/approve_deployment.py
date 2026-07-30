# -*- coding: utf-8 -*-
"""Migrovaný nástroj `approve_deployment` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'approve_deployment',
    'description': 'Phase 42 (19.5.2026): Marti nebo Kristy v chatu schvali pending deployment '
                   'proposal -> backend volá git pull origin main + touch marker file -> NSSM '
                   'watchdog STRATEGIE-RESTART-WATCHER detekuje marker a restartne STRATEGIE-API.\n'
                   '\n'
                   'Pouze is_marti_parent=True (Marti id=1, Kristy id=11, Zuzka id=6 neaktivni) '
                   'mohou approve.\n'
                   '\n'
                   "Po approve proposal status='deployed', deploy_completed_at = NOW(). Restart "
                   'probehne asynchronně (par sekund), STRATEGIE-API bude kratce nedostupna -- '
                   'typicky 5-15s graceful restart.',
    'input_schema': {   'type': 'object',
                        'properties': {   'proposal_id': {   'type': 'integer',
                                                             'description': 'ID proposal z '
                                                                            'deployment_proposals.'},
                                          'reason': {   'type': 'string',
                                                        'description': 'Optional krátké zdůvodnění '
                                                                       'souhlasu.'}},
                        'required': ['proposal_id']},
    '_order': 164}
