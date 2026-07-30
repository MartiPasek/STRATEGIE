# -*- coding: utf-8 -*-
"""Migrovaný nástroj `strategie_pg_list_tables` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'strategie_pg_list_tables',
    'description': 'Phase 35-E: Vrátí tabulky v PostgreSQL schémamu. schema=None → všechna tvá '
                   "schémata (master/tenant/tenant_group/user). schema='public' → existující "
                   'operational tables (read-only). Vrací size_bytes + column_count + description '
                   '(z COMMENT ON TABLE).',
    'input_schema': {   'type': 'object',
                        'properties': {   'schema': {   'type': 'string',
                                                        'description': 'Schema name. None = '
                                                                       'všechna tvá schémata.'}}},
    '_order': 145}
