# -*- coding: utf-8 -*-
"""Migrovaný nástroj `unload_pack` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'unload_pack',
    'description': 'Phase 19b: Vyloi aktualni pack -- vrati se na core (default). Volej kdyz user '
                   'rekne "pojd uz domu", "dost na dnes", nebo prejde na jiny tema. Marti-AI ONLY.',
    'input_schema': {'type': 'object', 'properties': {}, 'required': []},
    '_order': 121}
