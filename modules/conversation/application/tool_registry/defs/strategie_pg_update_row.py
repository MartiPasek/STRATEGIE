# -*- coding: utf-8 -*-
"""Migrovaný nástroj `strategie_pg_update_row` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'strategie_pg_update_row',
    'description': 'Phase 38.4 (12.5.2026 vecer): UPDATE rows v PostgreSQL table. Funguje na '
                   'LIBOVOLNEM schematu, kde Marti-AI ma GRANT UPDATE — typicky: fw.* (Marti-AI je '
                   'owner), plus public.knowledge_topic / public.knowledge_entry (Phase knowledge '
                   'base, 19.5.2026 vecer — explicit GRANT). NENI to omezeno na '
                   'master/tenant/tenant_group/user schemata (ta jsou jen list_schemas validace).\n'
                   '\n'
                   "PRAVO NA ROZMYSL PRED CINEM (Marti-AI's pattern 7.5. vecer):\n"
                   '  1. Nejdriv volej s dry_run=True → vidis SQL preview + matched_count.\n'
                   '  2. Pak zopakuj s dry_run=False → commit + RETURNING *.\n'
                   '\n'
                   'Safety guards:\n'
                   '  • where MUSI byt non-empty dict (UPDATE bez WHERE = destruktivni, '
                   'blokovany).\n'
                   '  • dry_run default True (musis explicit dat False pro commit).\n'
                   '  • Vraci updated rows pres RETURNING *.\n'
                   '\n'
                   'Use case priklady:\n'
                   "  • fw.comp_type aktivace: schema='fw', table='comp_type',\n"
                   "    values={'status': 'active'}, where={'id': 2}\n"
                   "  • public.knowledge_entry update: schema='public',\n"
                   "    table='knowledge_entry', values={'body_md': '...',\n"
                   "    'updated_by_text': 'Marti-AI'}, where={'id': 1}\n"
                   '\n'
                   'Pro IN-clause volej dvakrat (po jednom id), nebo pres query_table → pak '
                   'update_row v batch.',
    'input_schema': {   'type': 'object',
                        'properties': {   'schema': {'type': 'string'},
                                          'table': {'type': 'string'},
                                          'values': {   'type': 'object',
                                                        'description': 'Dict {column: new_value} — '
                                                                       'co SET. Aplikuje na '
                                                                       'vsechny rows matching '
                                                                       'where.'},
                                          'where': {   'type': 'object',
                                                       'description': 'Dict {column: '
                                                                      'filter_value}, AND logic. '
                                                                      'MUSI byt non-empty (UPDATE '
                                                                      'bez WHERE blokovan).'},
                                          'dry_run': {   'type': 'boolean',
                                                         'description': 'True (default) = preview '
                                                                        'SQL + matched_count, bez '
                                                                        'UPDATE. False = execute + '
                                                                        'commit.',
                                                         'default': True}},
                        'required': ['schema', 'table', 'values', 'where']},
    '_order': 152}
