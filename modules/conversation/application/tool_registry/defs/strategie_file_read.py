# -*- coding: utf-8 -*-
"""Migrovaný nástroj `strategie_file_read` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'strategie_file_read',
    'description': 'Phase 39: Precte obsah souboru v STRATEGIE projektu. Read everywhere (deny '
                   'list applied -- secrets blokovane).\n'
                   '\n'
                   'Limit: 10 MB (vetsi soubory -> error size_cap, pouzij specializovany tool nebo '
                   'split).\n'
                   '\n'
                   "encoding='utf-8' (default) -> text content + lines count.\n"
                   "encoding='cp1250' -> Windows legacy text (Marti-AI's gotcha #80).\n"
                   "encoding='base64' -> binary (obrazky, exe -- vraci base64 string).\n"
                   '\n'
                   'Pouziti: precti CLAUDE.md pro orient po amnesii, modules/erp/api/router.py pro '
                   'audit logiky, docs/CLAUDE_TECH.md pro gotcha lookup, marti_workspace/drafts/ '
                   'pro pokracovani v rozdelane praci.',
    'input_schema': {   'type': 'object',
                        'properties': {   'path': {   'type': 'string',
                                                      'description': 'Relative path k souboru '
                                                                     'uvnitr project_root. Path '
                                                                     'traversal + deny list '
                                                                     'enforced.'},
                                          'encoding': {   'type': 'string',
                                                          'description': "'utf-8' (default text), "
                                                                         "'cp1250' (Windows "
                                                                         "legacy), 'base64' "
                                                                         '(binary).',
                                                          'default': 'utf-8'}},
                        'required': ['path']},
    '_order': 158}
