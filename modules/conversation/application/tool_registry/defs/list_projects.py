# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_projects` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_projects',
    'description': 'VŽDY zavolej tento nástroj kdykoli uživatel chce vědět jaké projekty má. NIKDY '
                   'nesměř po paměti z předchozí konverzace — projekty se mění (nové, archivace, '
                   "přejmenování, aktivita), musíš mít čerstvé data. Spouštěče: 'jaké mám "
                   "projekty', 'co je v práci', 'ukaž mi projekty', 'co mam za projekty', 'a "
                   "projekty?', 'a co projekty'. Nástroj sám vrátí číslovaný seznam s pokyny pro "
                   'výběr — ZOBRAZ jeho výstup uživateli BEZ ÚPRAV (číslování je důležité, user '
                   'pak může napsat jen číslo pro přepnutí). Parametr nepotřebuje.',
    'input_schema': {'type': 'object', 'properties': {}},
    '_order': 38}
