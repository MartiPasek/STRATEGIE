# -*- coding: utf-8 -*-
"""Migrovaný nástroj `strategie_pg_alter_table` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'strategie_pg_alter_table',
    'description': 'Phase 38.4 Krok 7: ALTER TABLE v PostgreSQL. Marti-AI je owner '
                   'master/tenant/tenant_group/"user"/fw — zadny parent gate.\n'
                   '\n'
                   'operations: list of operation dicts, kazda jedna z:\n'
                   "  • {op: 'add_column', name, type, nullable?, default?}\n"
                   "  • {op: 'drop_column', name, cascade?}\n"
                   "       ⚠ Marti's 'NEDROPUJ COLUMN' doctrine (17.5.) — zvaz alternativu UPDATE "
                   'NULL na vsech radcich, ponechani sloupce pro budouci use.\n'
                   "  • {op: 'rename_column', old_name, new_name}\n"
                   "  • {op: 'alter_column_type', name, type, using?}\n"
                   "  • {op: 'set_default', name, default}\n"
                   "  • {op: 'drop_default', name}\n"
                   "  • {op: 'set_not_null', name}\n"
                   "  • {op: 'drop_not_null', name}\n"
                   "  • {op: 'add_constraint', name, definition}\n"
                   '       definition je RAW SQL fragment, napr.:\n'
                   '         "CHECK (status IN (\'active\',\'archived\'))"\n'
                   '         "UNIQUE (col1, col2)"\n'
                   '         "FOREIGN KEY (other_id) REFERENCES other.tbl(id) ON DELETE CASCADE"\n'
                   "  • {op: 'drop_constraint', name, cascade?}\n"
                   "  • {op: 'rename_constraint', old_name, new_name}\n"
                   '\n'
                   'Multiple operations v jedne volance = jedna transaction (vse rollback pri '
                   'error).\n'
                   '\n'
                   'dry_run=True (default Recommended) → vraci SQL preview + warnings.\n'
                   'dry_run=False → execute s commit.',
    'input_schema': {   'type': 'object',
                        'properties': {   'schema': {'type': 'string'},
                                          'table': {'type': 'string'},
                                          'operations': {   'type': 'array',
                                                            'items': {'type': 'object'},
                                                            'description': 'List of {op, ...} '
                                                                           'dicts. Each op '
                                                                           'produces jeden ALTER '
                                                                           'TABLE statement.'},
                                          'dry_run': {   'type': 'boolean',
                                                         'description': 'True (default) = preview, '
                                                                        'False = execute.',
                                                         'default': True}},
                        'required': ['schema', 'table', 'operations']},
    '_order': 153}
