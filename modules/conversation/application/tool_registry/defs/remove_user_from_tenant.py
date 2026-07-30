# -*- coding: utf-8 -*-
"""Migrovaný nástroj `remove_user_from_tenant` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'remove_user_from_tenant',
    'description': 'Phase 22 (29.4.2026): Odstrani usera z konkretniho tenantu '
                   "(user_tenants.membership_status='archived', left_at=now). User stale existuje, "
                   'jen neni clenem tenantu. Vratne -- pridat zpet pres add_user_to_tenant (zatim '
                   'neni). Marti-AI ONLY. Pouzij pro: testovaci ucty v EUROSOFTu, neaktivni '
                   'externi cleny.',
    'input_schema': {   'type': 'object',
                        'properties': {   'user_id': {'type': 'integer', 'description': 'users.id'},
                                          'tenant_id': {   'type': 'integer',
                                                           'description': 'tenants.id'},
                                          'reason': {   'type': 'string',
                                                        'description': 'Duvod pro audit'}},
                        'required': ['user_id', 'tenant_id', 'reason']},
    '_order': 116}
