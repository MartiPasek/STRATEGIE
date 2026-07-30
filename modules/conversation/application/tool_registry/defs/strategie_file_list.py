# -*- coding: utf-8 -*-
"""Migrovaný nástroj `strategie_file_list` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'strategie_file_list',
    'description': 'Phase 39: Vypise obsah adresare v STRATEGIE projektu (D:/Projekty/STRATEGIE/). '
                   'Read everywhere -- vidis vsechno krome deny list patternu (.env, .git/, '
                   'secrets/, *.key, node_modules/, build/, dist/, __pycache__/ a podobne).\n'
                   '\n'
                   "path='' (default) = project root. path='modules/erp/' = subadresar.\n"
                   'recursive=True = walk celym stromem (max 1000 entries, truncated flag pri '
                   'prekroceni).\n'
                   '\n'
                   "Vraci items: [{name, type: 'dir'|'file', size, modified, rel_path}].\n"
                   'Pouzij na zacatku navigace projektem nebo pro orientaci v marti_workspace/ pri '
                   'vyzvedavani draftu/analysis.',
    'input_schema': {   'type': 'object',
                        'properties': {   'path': {   'type': 'string',
                                                      'description': 'Relative path uvnitr '
                                                                     "project_root. '' (default) = "
                                                                     "root. Akceptuje '/' i '\\' "
                                                                     'separator. Path traversal '
                                                                     '(..) blokovan.',
                                                      'default': ''},
                                          'recursive': {   'type': 'boolean',
                                                           'description': 'True = rekurzivni walk '
                                                                          'subtree. False '
                                                                          '(default) = jen primy '
                                                                          'obsah adresare.',
                                                           'default': False}}},
    '_order': 157}
