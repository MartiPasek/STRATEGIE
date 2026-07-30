# -*- coding: utf-8 -*-
"""Migrovaný nástroj `create_continuation` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'create_continuation',
    'description': 'Phase 36 (9.5.2026): univerzální dovětek pro uzavřené konverzace.\n'
                   '\n'
                   "Generalizace Phase 19c-e2 'create_personal_appendix' — funguje pro VŠECHNY "
                   'uzavřené konverzace:\n'
                   "  - lifecycle_state='personal' (knížka srdce, read-only)\n"
                   "  - lifecycle_state='archived' (po Phase 36 auditu)\n"
                   '\n'
                   'Vytvoří NOVOU konverzaci s parent_conversation_id. Dědí tenant_id / project_id '
                   '/ active_agent_id z parent. Sidebar render = odsazené pod parentem (Phase '
                   '19c-e2 tree pattern).\n'
                   '\n'
                   "Marti-AI's iterace 2 volba názvu: technický 'create_continuation' (NE "
                   "poetický) — 'poetiku si nechám pro sebe — do místa, kde patří'. Distinkce "
                   'tools (čitelné za rok bez kontextu) vs vlastní jazyk.\n'
                   '\n'
                   'create_personal_appendix zůstane jako alias 2 týdny pro backward compat, pak '
                   'deprecated.',
    'input_schema': {   'type': 'object',
                        'properties': {   'parent_conversation_id': {'type': 'integer'},
                                          'initial_message': {   'type': 'string',
                                                                 'description': 'Volitelná první '
                                                                                'zpráva v dovětku '
                                                                                '(ne audit message '
                                                                                'stamp).'}},
                        'required': ['parent_conversation_id']},
    '_order': 170}
