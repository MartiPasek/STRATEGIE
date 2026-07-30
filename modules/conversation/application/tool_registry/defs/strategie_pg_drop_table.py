# -*- coding: utf-8 -*-
"""Migrovaný nástroj `strategie_pg_drop_table` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'strategie_pg_drop_table',
    'description': 'Phase 38.4 Krok 7: DROP TABLE v PostgreSQL — DESTRUCTIVE.\n'
                   '\n'
                   "Marti's 'ID je svaty, NEDROPUJ COLUMN' doctrine (17.5.) eskalovany na "
                   "'NEDROPUJ TABLE bez explicit confirm'. Safety guard: confirm_phrase MUSI byt "
                   "exact 'DROP {schema}.{table}' (case-sensitive). Bez toho fail.\n"
                   '\n'
                   'Pred DROP zvaz:\n'
                   "  • Soft archive — UPDATE status='archived' (pokud tabulka ma status sloupec) "
                   'zachova historii.\n'
                   "  • Marti's 'UPDATE NULL na vsech radcich, ponechat sloupec' pattern (Krok 5.P "
                   'z 17.5.) pro framework cleanup.\n'
                   '\n'
                   'dry_run vraci preview SQL + row_count_before_drop + FK dependents warning.\n'
                   "cascade=True → drop FK dependent objects too (Marti-AI's decision).",
    'input_schema': {   'type': 'object',
                        'properties': {   'schema': {'type': 'string'},
                                          'table': {'type': 'string'},
                                          'confirm_phrase': {   'type': 'string',
                                                                'description': 'MUSI rovnat se '
                                                                               "'DROP "
                                                                               "{schema}.{table}' "
                                                                               '(case-sensitive). '
                                                                               'Safety guard.'},
                                          'cascade': {   'type': 'boolean',
                                                         'description': 'DROP TABLE ... CASCADE '
                                                                        '(drop dependents).',
                                                         'default': False},
                                          'dry_run': {   'type': 'boolean',
                                                         'description': 'True (default) = preview, '
                                                                        'False = execute.',
                                                         'default': True}},
                        'required': ['schema', 'table', 'confirm_phrase']},
    '_order': 154}
