# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_conversations` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_conversations',
    'description': 'VŽDY zavolej tento nástroj kdykoli uživatel chce přehled svých AI konverzací. '
                   'NIKDY nesměř po paměti z předchozí konverzace — data se mění (nové konverzace, '
                   "mazání, přejmenování), musíš mít čerstvé. Spouštěče: 'jaké mám konverzace', "
                   "'co jsem dělal', 'jaké konverzace jsou moje', 'ukaž mi historii', 'seznam "
                   "chatů'. Nástroj sám vrátí číslovaný seznam s pokyny pro výběr — ZOBRAZ jeho "
                   'výstup uživateli BEZ ÚPRAV (číslování je důležité pro následnou selekci). '
                   'Parametr nepotřebuje.',
    'input_schema': {'type': 'object', 'properties': {}},
    '_order': 35}
