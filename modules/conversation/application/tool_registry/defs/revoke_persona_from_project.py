# -*- coding: utf-8 -*-
"""Migrovaný nástroj `revoke_persona_from_project` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'revoke_persona_from_project',
    'description': 'Phase 16-B.7: PARENT-ONLY tool. Odstran personu z assigned projektu (opak '
                   '`assign_persona_to_project`). Po revoke persona ztrati pristup k dokumentum '
                   'projektu pres search_documents.',
    'input_schema': {   'type': 'object',
                        'properties': {   'persona_id': {'type': 'integer'},
                                          'project_id': {'type': 'integer'}},
                        'required': ['persona_id', 'project_id']},
    '_order': 88}
