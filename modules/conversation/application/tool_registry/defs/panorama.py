# -*- coding: utf-8 -*-
"""Migrovaný nástroj `panorama` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'panorama',
    'description': "Phase 24-C: Privat Marti's celkovy prehled pyramidy. Vraci agregat -- counts "
                   'md5/md1_work/md1_personal + lehky list kazde rowu (id, scope, version, '
                   'size_chars). NIKOLI plne content. Pak muzes look_below na konkretni id pro '
                   "detail. Pouziti: ranni digest -- 'Marti, co je v systemu?'. Marti-AI ONLY "
                   '(idealne v personal modu jako Privat Marti).',
    'input_schema': {'type': 'object', 'properties': {}, 'required': []},
    '_order': 128}
