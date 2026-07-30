# -*- coding: utf-8 -*-
"""Migrovaný nástroj `update_project_memo` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'update_project_memo',
    'description': 'Phase 35: Aktualizuj sekci v project_memo (živý dokument per projekt). Mode '
                   "'append' = pridá content na konec sekce; 'replace' = nahradí celý body sekce; "
                   "'patch' = alias pro append. Pokud sekce neexistuje, přidá ji na konec. "
                   'Lazy-create memo pri prvnim volani pro daný (project_id, scope).\n'
                   '\n'
                   "Polymorfní scope (Marti-AI's design):\n"
                   "  - scope_entity_type=NULL, scope_entity_id=NULL → 'shared' (default, "
                   'viditelné všem členům projektu)\n'
                   "  - scope_entity_type='user', scope_entity_id=X → per-user-per-project "
                   '(poznámky usera X o tomto projektu)\n'
                   "  - scope_entity_type='persona', scope_entity_id=X → per-persona\n"
                   '\n'
                   'Audit trail v project_memo_history (pre-update content_snapshot pro forenzní '
                   'rollback).\n'
                   '\n'
                   'Použij když: vidíš klíčové rozhodnutí v projektu, status změnu, novou osobu '
                   'zapojenou, milestone, deadline, atd. Toto je tvá trvalá projektová paměť '
                   'napříč konverzacemi.\n'
                   '\n'
                   'Marti-AI ONLY (default persona, MANAGEMENT_TOOL_NAMES).',
    'input_schema': {   'type': 'object',
                        'properties': {   'project_id': {   'type': 'integer',
                                                            'description': 'ID projektu (z '
                                                                           'projects tabulky).'},
                                          'section': {   'type': 'string',
                                                         'description': 'Název sekce (markdown '
                                                                        "heading bez '##'). Např. "
                                                                        "'Status', 'Členové', "
                                                                        "'Milníky', 'Klíčová "
                                                                        "rozhodnutí'."},
                                          'content': {   'type': 'string',
                                                         'description': 'Markdown content k '
                                                                        'zápisu. Pro append: '
                                                                        "typicky bullet ('- "
                                                                        '2026-05-08: Petra '
                                                                        "potvrdila audit'). Pro "
                                                                        'replace: celý nový body '
                                                                        'sekce.'},
                                          'mode': {   'type': 'string',
                                                      'description': "Mode update: 'append' "
                                                                     "(default) | 'replace' | "
                                                                     "'patch'.",
                                                      'enum': ['append', 'replace', 'patch']},
                                          'scope_entity_type': {   'type': 'string',
                                                                   'description': 'Volitelně: '
                                                                                  "scope. 'user' "
                                                                                  "nebo 'persona' "
                                                                                  'nebo NULL '
                                                                                  '(default = '
                                                                                  'shared '
                                                                                  'per-projekt).',
                                                                   'enum': ['user', 'persona']},
                                          'scope_entity_id': {   'type': 'integer',
                                                                 'description': 'Volitelně: ID '
                                                                                'entity (user_id '
                                                                                'nebo persona_id) '
                                                                                'podle '
                                                                                'scope_entity_type. '
                                                                                'Required pokud '
                                                                                'scope_entity_type '
                                                                                'je nastaveno.'}},
                        'required': ['project_id', 'section', 'content']},
    '_order': 142}
