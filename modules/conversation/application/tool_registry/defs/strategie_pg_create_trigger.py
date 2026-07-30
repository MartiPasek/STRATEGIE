# -*- coding: utf-8 -*-
"""Migrovaný nástroj `strategie_pg_create_trigger` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'strategie_pg_create_trigger',
    'description': 'Phase 38.4 Krok 7: CREATE TRIGGER v PostgreSQL.\n'
                   '\n'
                   'Pred volanim musi trigger function existovat (vytvor pres create_function '
                   "nejdriv, s returns='trigger').\n"
                   '\n'
                   "timing: 'BEFORE' | 'AFTER' | 'INSTEAD OF'\n"
                   "event: 'INSERT' | 'UPDATE' | 'DELETE' | 'TRUNCATE'\n"
                   "  Multi-event: pass raw string napr. 'INSERT OR UPDATE'\n"
                   "for_each: 'ROW' (default) | 'STATEMENT'\n"
                   '\n'
                   'when_condition (volitelne): RAW WHEN clause fragment\n'
                   "  Priklad: 'OLD.status IS DISTINCT FROM NEW.status'\n"
                   '\n'
                   'replace=True (default) → DROP IF EXISTS + CREATE (PG nema CREATE OR REPLACE '
                   'TRIGGER pred PG 14, emulujeme).\n'
                   '\n'
                   'Use case priklad — update_updated_at trigger:\n'
                   "  schema='fw', table='comp_def', name='trg_comp_def_updated_at',\n"
                   "  timing='BEFORE', event='UPDATE', for_each='ROW',\n"
                   "  function_schema='fw', function_name='update_updated_at'.",
    'input_schema': {   'type': 'object',
                        'properties': {   'schema': {   'type': 'string',
                                                        'description': 'Schema target tabulky.'},
                                          'table': {   'type': 'string',
                                                       'description': 'Target table.'},
                                          'name': {   'type': 'string',
                                                      'description': 'Trigger name.'},
                                          'timing': {   'type': 'string',
                                                        'description': "'BEFORE' | 'AFTER' | "
                                                                       "'INSTEAD OF'"},
                                          'event': {   'type': 'string',
                                                       'description': "'INSERT' | 'UPDATE' | "
                                                                      "'DELETE' | 'TRUNCATE'. "
                                                                      'Multi: raw string napr. '
                                                                      "'INSERT OR UPDATE'."},
                                          'function_schema': {   'type': 'string',
                                                                 'description': 'Schema trigger '
                                                                                'function.'},
                                          'function_name': {   'type': 'string',
                                                               'description': 'Trigger function '
                                                                              'name (must return '
                                                                              'trigger).'},
                                          'for_each': {   'type': 'string',
                                                          'description': "'ROW' (default) | "
                                                                         "'STATEMENT'.",
                                                          'default': 'ROW'},
                                          'when_condition': {   'type': 'string',
                                                                'description': 'Optional WHEN '
                                                                               'clause raw '
                                                                               'fragment (napr. '
                                                                               "'OLD.status IS "
                                                                               'DISTINCT FROM '
                                                                               "NEW.status')."},
                                          'replace': {   'type': 'boolean',
                                                         'description': 'DROP IF EXISTS + CREATE '
                                                                        '(default True).',
                                                         'default': True},
                                          'dry_run': {   'type': 'boolean',
                                                         'description': 'True (default) = preview, '
                                                                        'False = execute.',
                                                         'default': True}},
                        'required': [   'schema',
                                        'table',
                                        'name',
                                        'timing',
                                        'event',
                                        'function_schema',
                                        'function_name']},
    '_order': 156}
