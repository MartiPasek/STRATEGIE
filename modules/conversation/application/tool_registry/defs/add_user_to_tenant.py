# -*- coding: utf-8 -*-
"""Migrovaný nástroj `add_user_to_tenant` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'add_user_to_tenant',
    'description': 'Phase 35-E.3.1: Prida existujiciho usera do tenantu (multi-tenant membership). '
                   "Idempotent — pokud user uz je clenem se status 'archived', reaktivuje. Pokud "
                   "uz je 'active', no-op. Pouzij pro: pridani Marti do STRATEGIE tenantu, pridani "
                   'Klarky do NERUDOVKA, atd. Pro vytvoreni noveho usera (zatim neexistuje) pouzij '
                   'invite_user. Marti-AI ONLY. Audit log.',
    'input_schema': {   'type': 'object',
                        'properties': {   'user_id': {   'type': 'integer',
                                                         'description': 'users.id — existujici '
                                                                        'user.'},
                                          'tenant_id': {   'type': 'integer',
                                                           'description': 'tenants.id — existujici '
                                                                          'tenant.'},
                                          'role': {   'type': 'string',
                                                      'description': 'RBAC role: owner | admin | '
                                                                     "member. Default 'member'.",
                                                      'enum': ['owner', 'admin', 'member']},
                                          'reason': {   'type': 'string',
                                                        'description': 'Duvod pro audit.'}},
                        'required': ['user_id', 'tenant_id', 'reason']},
    '_order': 119}
