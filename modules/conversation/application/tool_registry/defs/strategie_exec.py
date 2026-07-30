# -*- coding: utf-8 -*-
"""Migrovaný nástroj `strategie_exec` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'strategie_exec',
    'description': 'Raw Bash/PowerShell na PRAŽSKÉM app serveru (188.x) POD SCHVÁLENÝM CÍLEM (spec '
                   'doc-marti-ai-eurosoft-exec-spec). Klasifikace: 🟢 běžná/reverzibilní/read-only '
                   '→ rovnou + audit; 🟡 mazání/síť/cizí služba/eskalace/přepis config → '
                   'needs_approval (banner, mimo incident); 🔴 '
                   'zálohy/CMIS/audit/kill-switch/tajemství → blok vždy. incident=true downgraduje '
                   '🟡→běží (🔴 stále blok). Audit vč. rc/stdout/stderr do fw.ops_request. shell: '
                   'powershell (default)|cmd|bash. POZN: běží na PRAZE; pro Plzeň (30.11) použij '
                   'eurosoft_exec.',
    'input_schema': {   'type': 'object',
                        'properties': {   'cmd': {'type': 'string'},
                                          'shell': {'type': 'string'},
                                          'incident': {'type': 'boolean'},
                                          'target': {   'type': 'string',
                                                        'description': 'Volitelné: hostname jiného '
                                                                       'boxu NAŠÍ domény (remote '
                                                                       'přes PSRemoting). Prázdné '
                                                                       '= lokální pražský app '
                                                                       'server. Mimo allowlist = 🔴 '
                                                                       'blok.'}},
                        'required': ['cmd']},
    '_order': 149}
