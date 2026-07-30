# -*- coding: utf-8 -*-
"""Migrovaný nástroj `strategie_pg_query_raw` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'strategie_pg_query_raw',
    'description': 'Phase 35-E: Read-only raw PostgreSQL SQL. WHITELIST: jen '
                   'SELECT/WITH/EXPLAIN/SHOW. Pro DDL/DML použij dedicated tools (create_table, '
                   'insert_row, ...).\n'
                   '\n'
                   'Použij pro composite queries (JOIN, GROUP BY, agregace) které query_table '
                   "neumí. Příklad: SELECT count(*) FROM fw.entity_def WHERE tier = 'master' GROUP "
                   'BY is_active.',
    'input_schema': {   'type': 'object',
                        'properties': {   'sql': {   'type': 'string',
                                                     'description': 'SELECT / WITH / EXPLAIN / '
                                                                    'SHOW SQL.'},
                                          'params': {   'type': 'object',
                                                        'description': 'Volitelné parametrizace '
                                                                       '{param_name: value}, v SQL '
                                                                       'referenced jako '
                                                                       ':param_name.'}},
                        'required': ['sql']},
    '_order': 150}
