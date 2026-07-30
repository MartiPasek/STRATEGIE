# -*- coding: utf-8 -*-
"""Migrovaný nástroj `reject_lifecycle_suggestion` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'reject_lifecycle_suggestion',
    'description': "Phase 15d: Zamitni lifecycle suggestion (Marti rekl 'ne, necham aktivni'). "
                   'Vrati lifecycle_state na NULL = active.',
    'input_schema': {'type': 'object', 'properties': {}},
    '_order': 71}
