# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_tenants` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_tenants',
    'description': 'Phase 35-E.3.1: Vrati seznam tenantu v systemu. Rodic vidi vse, non-rodic jen '
                   'aktivni clenstvi. Sloupce: id, tenant_name, tenant_code, tenant_type, status, '
                   'owner_user_id, created_at, member_count. Pouzij pro orientaci pred '
                   'create_tenant nebo add_user_to_tenant. Marti-AI ONLY.',
    'input_schema': {   'type': 'object',
                        'properties': {   'include_inactive': {   'type': 'boolean',
                                                                  'description': 'True = vrati i '
                                                                                 'archived/disabled '
                                                                                 'tenanty. Default '
                                                                                 'false.'}}},
    '_order': 117}
