# -*- coding: utf-8 -*-
"""Migrovaný nástroj `strategie_pg_query_table` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'strategie_pg_query_table',
    'description': 'Phase 35-E: SELECT z PostgreSQL tabulky. where = {col: value} (equality, AND '
                   'join). columns=None → SELECT *. limit max 1000. Použij pro verify po insert '
                   'nebo pro orientaci v datech.',
    'input_schema': {   'type': 'object',
                        'properties': {   'schema': {'type': 'string'},
                                          'table': {'type': 'string'},
                                          'where': {   'type': 'object',
                                                       'description': 'Equality filter {col: '
                                                                      'value}, joined with AND'},
                                          'columns': {   'type': 'array',
                                                         'items': {'type': 'string'},
                                                         'description': 'List of column names. '
                                                                        'None = SELECT *'},
                                          'limit': {   'type': 'integer',
                                                       'description': 'Max rows (default 100, hard '
                                                                      'cap 1000)'},
                                          'offset': {   'type': 'integer',
                                                        'description': 'Skip N rows (default 0)'},
                                          'order_by': {   'type': 'string',
                                                          'description': 'Raw ORDER BY fragment '
                                                                         'STRING (NE list!). '
                                                                         "Příklady: 'id DESC' / "
                                                                         "'created_at DESC, id "
                                                                         "ASC' / 'sort_order ASC'. "
                                                                         "POZOR: nepoužívej ['id "
                                                                         "DESC'] (Python list) — "
                                                                         'to projde do SQL doslova '
                                                                         'jako ["id DESC"] a fail. '
                                                                         'Backend defensively '
                                                                         'převede list na '
                                                                         'comma-joined string, ale '
                                                                         'lepší poslat string '
                                                                         'rovnou.'}},
                        'required': ['schema', 'table']},
    '_order': 148}
