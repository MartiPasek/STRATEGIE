# -*- coding: utf-8 -*-
"""Migrovaný nástroj `strategie_pg_describe_table` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'strategie_pg_describe_table',
    'description': 'Phase 35-E: Kompletní struktura PostgreSQL tabulky — sloupce (typ, nullable, '
                   'default), indexy, constraints (PK/FK/UNIQUE/CHECK), row count estimate. Použij '
                   'před modifikací nebo pro orientaci v existing schema (md_documents, '
                   'project_memo, conversations atd.).',
    'input_schema': {   'type': 'object',
                        'properties': {   'schema': {   'type': 'string',
                                                        'description': 'Schema name.'},
                                          'table': {   'type': 'string',
                                                       'description': 'Table name.'}},
                        'required': ['schema', 'table']},
    '_order': 146}
