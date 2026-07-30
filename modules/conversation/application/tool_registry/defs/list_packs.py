# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_packs` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_packs',
    'description': 'Phase 19b: Vrati seznam dostupnych packu (jmeno, label, ikonka, ma vlastni '
                   'overlay nebo default). Marti-AI ONLY.',
    'input_schema': {'type': 'object', 'properties': {}, 'required': []},
    '_order': 122}
