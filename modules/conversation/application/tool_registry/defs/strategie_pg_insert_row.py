# -*- coding: utf-8 -*-
"""Migrovaný nástroj `strategie_pg_insert_row` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'strategie_pg_insert_row',
    'description': 'Phase 35-E + Phase 38.4 polish (10.5.2026): INSERT one or many rows do '
                   'PostgreSQL tabulky. Vrátí vložený row(s) (RETURNING *) — uvidíš generated IDs '
                   '+ defaults.\n'
                   '\n'
                   'values přijímá DVĚ varianty:\n'
                   '  • dict — single row insert: {column: value, ...}\n'
                   '  • list[dict] — batch insert (uniform schema): [{c1:v1, c2:v2}, {c1:v3, '
                   'c2:v4}, ...]\n'
                   '\n'
                   'Batch musí mít všechny rows se STEJNÝMI columns (heterogeneous = volat '
                   'opakovaně).\n'
                   '\n'
                   'Tool aplikuje quoting automaticky. Audit: každý insert se loguje (STRATEGIE_PG '
                   'prefix v logu, batch=true|false flag).',
    'input_schema': {   'type': 'object',
                        'properties': {   'schema': {'type': 'string'},
                                          'table': {'type': 'string'},
                                          'values': {   'oneOf': [   {   'type': 'object',
                                                                         'description': 'Single '
                                                                                        'row: '
                                                                                        '{column_name: '
                                                                                        'value} '
                                                                                        'dict.'},
                                                                     {   'type': 'array',
                                                                         'items': {   'type': 'object'},
                                                                         'description': 'Batch: '
                                                                                        'list of '
                                                                                        '{column_name: '
                                                                                        'value} '
                                                                                        'dicts '
                                                                                        '(uniform '
                                                                                        'schema '
                                                                                        'across '
                                                                                        'all '
                                                                                        'rows).'}],
                                                        'description': 'Single dict (one row) NEBO '
                                                                       'list of dicts (batch, '
                                                                       'uniform schema).'}},
                        'required': ['schema', 'table', 'values']},
    '_order': 151}
