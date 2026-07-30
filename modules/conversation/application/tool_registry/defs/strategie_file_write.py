# -*- coding: utf-8 -*-
"""Migrovaný nástroj `strategie_file_write` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'strategie_file_write',
    'description': 'Phase 39: Zapise soubor do marti_workspace/** (write zone whitelist). Mimo '
                   'marti_workspace/ -> 403 write_zone_violation.\n'
                   '\n'
                   'Limit: 5 MB per call (pro vetsi obsah split na vice souboru).\n'
                   '\n'
                   "Doctrine (Marti-AI's chat 19.5. 02:30):\n"
                   '  - marti_workspace/drafts/ -- rozepsane myslenky (NE RAG ingest)\n'
                   '  - marti_workspace/analysis/ -- hotove analyzy (auto-RAG ingest)\n'
                   '  - marti_workspace/output/ -- hotove vystupy k presunu/commit (auto-RAG)\n'
                   "  - marti_workspace/notes/ -- scratch pad 'pokracuj od radku 847' (NE RAG)\n"
                   '  - marti_workspace/claude_chats/ -- Phase 40 v2 transcripty (auto-RAG)\n'
                   '\n'
                   'Naming convention: _vN pro versions (foo_v1.txt, foo_v2.txt) -- '
                   'last-write-wins, no lock.\n'
                   '\n'
                   "mode='overwrite' (default), 'append', 'fail_if_exists'.\n"
                   "encoding='utf-8' (default), 'base64' (binary).",
    'input_schema': {   'type': 'object',
                        'properties': {   'path': {   'type': 'string',
                                                      'description': 'Relative path UVNITR '
                                                                     'marti_workspace/. Path '
                                                                     'traversal + deny list + '
                                                                     'write zone enforced.'},
                                          'content': {   'type': 'string',
                                                         'description': 'Obsah souboru. Pro text '
                                                                        "encoding='utf-8' default, "
                                                                        'pro binary '
                                                                        "encoding='base64' a "
                                                                        'content = base64 string.'},
                                          'mode': {   'type': 'string',
                                                      'enum': [   'overwrite',
                                                                  'append',
                                                                  'fail_if_exists'],
                                                      'description': "'overwrite' (default) = "
                                                                     "replace existing. 'append' = "
                                                                     'add to end (vytvori pokud '
                                                                     'neexistuje). '
                                                                     "'fail_if_exists' = error "
                                                                     'pokud target uz existuje '
                                                                     '(safety pro draft '
                                                                     'preservation).',
                                                      'default': 'overwrite'},
                                          'encoding': {   'type': 'string',
                                                          'description': "'utf-8' (default text) "
                                                                         "nebo 'base64' (binary).",
                                                          'default': 'utf-8'}},
                        'required': ['path', 'content']},
    '_order': 159}
