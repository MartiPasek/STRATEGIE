# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_persona_project_access` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_persona_project_access',
    'description': 'Phase 16-B.7: Vraci aktualni ACL stav -- per-persona seznam assigned projektu. '
                   "Marti-AI default je oznacena jako 'rodic (bypass)'.\n"
                   '\n'
                   "**Pouzij** kdyz se uzivatel pta 'kdo k cemu ma pristup', 'jake projekty "
                   "Pravnik vidi'.",
    'input_schema': {   'type': 'object',
                        'properties': {   'persona_id': {   'type': 'integer',
                                                            'description': 'Volitelne -- pokud '
                                                                           'zadano, vrati access '
                                                                           'jen pro tu personu. '
                                                                           'Default vse.'}}},
    '_order': 89}
