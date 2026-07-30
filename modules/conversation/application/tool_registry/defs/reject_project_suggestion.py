# -*- coding: utf-8 -*-
"""Migrovaný nástroj `reject_project_suggestion` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'reject_project_suggestion',
    'description': "Phase 15c: Zamitni project suggestion (Marti rekl 'ne, necham'). Vyclear "
                   'suggested_project_id + reason + at.',
    'input_schema': {'type': 'object', 'properties': {}},
    '_order': 70}
