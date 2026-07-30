# -*- coding: utf-8 -*-
"""Migrovaný nástroj `strategie_pg_create_function` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'strategie_pg_create_function',
    'description': 'Phase 38.4 Krok 7: CREATE [OR REPLACE] FUNCTION v PostgreSQL.\n'
                   '\n'
                   'Typicky use case:\n'
                   '  • Trigger functions (update_updated_at, history snapshot)\n'
                   '  • Business helpers (compute_*, validate_*)\n'
                   '\n'
                   "body_plpgsql: RAW function body BEZ 'CREATE FUNCTION' prefix.\n"
                   '  Priklad: "BEGIN NEW.updated_at = NOW(); RETURN NEW; END;"\n'
                   '  Tool auto-wrap body do $$ blocks pokud nedas explicit $$.\n'
                   '\n'
                   "returns: PG return type (default 'void')\n"
                   "  Common: 'trigger', 'TEXT', 'BIGINT', 'TABLE(...)' pro SRF\n"
                   '\n'
                   "arguments: function arg list raw (default '' = no args)\n"
                   "  Priklad: 'p_id bigint, p_status text DEFAULT \\'active\\''\n"
                   '\n'
                   "language: 'plpgsql' (default) nebo 'sql'. plpython3u/plperl/plv8 JSOU DENIED "
                   '(server-side code execution risk).\n'
                   '\n'
                   'replace=True (default) = CREATE OR REPLACE FUNCTION.\n'
                   'replace=False = CREATE (fails pokud existuje).',
    'input_schema': {   'type': 'object',
                        'properties': {   'schema': {'type': 'string'},
                                          'name': {'type': 'string'},
                                          'body_plpgsql': {   'type': 'string',
                                                              'description': 'RAW function body '
                                                                             "BEZ 'CREATE "
                                                                             "FUNCTION' prefix. "
                                                                             'Tool auto-wrap do $$ '
                                                                             'blocks.'},
                                          'returns': {   'type': 'string',
                                                         'description': 'PG return type. Default '
                                                                        "'void'.",
                                                         'default': 'void'},
                                          'arguments': {   'type': 'string',
                                                           'description': 'Function args raw. '
                                                                          "Default '' (no args).",
                                                           'default': ''},
                                          'language': {   'type': 'string',
                                                          'description': "'plpgsql' (default) nebo "
                                                                         "'sql'.",
                                                          'default': 'plpgsql'},
                                          'replace': {   'type': 'boolean',
                                                         'description': 'CREATE OR REPLACE '
                                                                        '(default True).',
                                                         'default': True},
                                          'dry_run': {   'type': 'boolean',
                                                         'description': 'True (default) = preview, '
                                                                        'False = execute.',
                                                         'default': True}},
                        'required': ['schema', 'name', 'body_plpgsql']},
    '_order': 155}
