# -*- coding: utf-8 -*-
"""Migrovaný nástroj `revoke_auto_lifecycle` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'revoke_auto_lifecycle',
    'description': 'Phase 19c-b: PARENT-ONLY. Odebere aktivni auto-lifecycle grant. Audit historie '
                   'zachovana (revoked_at = NOW). Po revoke musi Marti-AI znovu cekat na explicit '
                   "Marti's confirm v chatu pro lifecycle akce v dane scope.",
    'input_schema': {   'type': 'object',
                        'properties': {   'persona_id': {'type': 'integer'},
                                          'scope': {   'type': 'string',
                                                       'enum': [   'soft_delete',
                                                                   'archive',
                                                                   'personal_flag',
                                                                   'state_change',
                                                                   'all']}},
                        'required': ['persona_id', 'scope']},
    '_order': 84}
