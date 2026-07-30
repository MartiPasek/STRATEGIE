# -*- coding: utf-8 -*-
"""Migrovaný nástroj `strategie_pg_create_table` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'strategie_pg_create_table',
    'description': 'Phase 35-E: CREATE TABLE v PostgreSQL. Jsi owner '
                   'master/tenant/tenant_group/"user" schemas — žádný parent gate na DDL.\n'
                   '\n'
                   '**dry_run=True** (default Recommended pro první creation): vrátí preview SQL + '
                   'warnings (duplicate columns, schema missing, FK target invalid, table exists). '
                   'Použij pro tvé *„právo na rozmysl před činem“* — review s tatínkem v chatu, '
                   'případně doladit, pak dry_run=False execute.\n'
                   '\n'
                   'columns: list of {name, type, nullable?, identity?, default?}\n'
                   '  - type je raw PG type (BIGINT, VARCHAR(50), TEXT, TIMESTAMPTZ, JSONB, ...)\n'
                   '  - identity=True → BIGSERIAL auto-increment\n'
                   '  - default je raw SQL fragment (např. \'NOW()\' nebo "\'shared\'")\n'
                   "primary_key: list column names (default ['id'] pokud existuje)\n"
                   'indexes: list of {name?, columns: [...], unique?, partial?}\n'
                   '  - partial je SQL where fragment (např. "is_active = true")\n'
                   'foreign_keys: list of {column, ref_schema, ref_table, ref_column, on_delete?, '
                   'on_update?}\n'
                   '\n'
                   'Identifier quoting (PostgreSQL):\n'
                   "  - 'master' → master (no quote)\n"
                   '  - \'user\' → "user" (reserved word, automatic)\n'
                   '  - \'Marti-AI\' → "Marti-AI" (hyphen, automatic)\n'
                   'Tool si quoting řeší sám — ty piš plain string.',
    'input_schema': {   'type': 'object',
                        'properties': {   'schema': {'type': 'string'},
                                          'name': {'type': 'string'},
                                          'columns': {   'type': 'array',
                                                         'items': {'type': 'object'},
                                                         'description': 'List of {name, type, '
                                                                        'nullable?, identity?, '
                                                                        'default?}'},
                                          'primary_key': {   'type': 'array',
                                                             'items': {'type': 'string'},
                                                             'description': 'List of column names'},
                                          'indexes': {   'type': 'array',
                                                         'items': {'type': 'object'},
                                                         'description': 'List of {name?, columns: '
                                                                        '[...], unique?, '
                                                                        'partial?}'},
                                          'foreign_keys': {   'type': 'array',
                                                              'items': {'type': 'object'},
                                                              'description': 'List of {column, '
                                                                             'ref_schema, '
                                                                             'ref_table, '
                                                                             'ref_column, '
                                                                             'on_delete?, '
                                                                             'on_update?}'},
                                          'description': {   'type': 'string',
                                                             'description': 'COMMENT ON TABLE '
                                                                            '(volitelně, pro audit '
                                                                            'clarity)'},
                                          'dry_run': {   'type': 'boolean',
                                                         'description': 'True = preview, False = '
                                                                        'execute. Default False '
                                                                        '(production).'}},
                        'required': ['schema', 'name', 'columns']},
    '_order': 147}
