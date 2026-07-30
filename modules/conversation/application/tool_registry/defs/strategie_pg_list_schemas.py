# -*- coding: utf-8 -*-
"""Migrovaný nástroj `strategie_pg_list_schemas` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'strategie_pg_list_schemas',
    'description': 'Phase 35-E: Vrátí PostgreSQL schémata, kde máš (Marti-AI) přístup. Tvá vlastní '
                   'schémata: master / tenant / tenant_group / "user" — všechna AUTHORIZATION '
                   "'Marti-AI' (jsi owner). Plus public (read-only operational tables — "
                   'md_documents, project_memo, conversations, atd.). \n'
                   '\n'
                   'Použij na začátku každé framework session — uvidíš co tam už je vs '
                   'missing_expected list.',
    'input_schema': {'type': 'object', 'properties': {}},
    '_order': 144}
