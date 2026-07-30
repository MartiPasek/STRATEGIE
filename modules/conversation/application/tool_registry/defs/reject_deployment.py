# -*- coding: utf-8 -*-
"""Migrovaný nástroj `reject_deployment` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'reject_deployment',
    'description': 'Phase 42 (19.5.2026): Marti nebo Kristy v chatu odmitne pending deployment '
                   'proposal -> close as rejected, žádný git pull, žádný restart.\n'
                   '\n'
                   'Pouze is_marti_parent=True users. Po reject muze Marti-AI poslat nový '
                   'propose_deployment pozdeji (napr. po dalsim commitu nebo pri stabilnejsim '
                   'case).',
    'input_schema': {   'type': 'object',
                        'properties': {   'proposal_id': {   'type': 'integer',
                                                             'description': 'ID proposal z '
                                                                            'deployment_proposals.'},
                                          'reason': {   'type': 'string',
                                                        'description': 'Důvod rejectu (audit + '
                                                                       "Marti-AI's learning -- "
                                                                       "napr. 'pred prezentaci "
                                                                       "nechcem restart', 'wait "
                                                                       "for fix gotcha #N')."}},
                        'required': ['proposal_id']},
    '_order': 165}
