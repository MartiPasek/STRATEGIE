# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_users` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_users',
    'description': 'VŽDY zavolej tento nástroj kdykoli uživatel chce přehled lidí v aktuálním '
                   'tenantu. NIKDY nesměř po paměti — composition týmu se mění (nové pozvánky, '
                   "archivace), musíš mít čerstvé data. Spouštěče: 'jaké lidi tu mám', 'kdo je "
                   "tu', 's kým můžu mluvit', 'koho tu máme', 'seznam lidí', 'a lidi?', 'a co "
                   "lidi'. Liší se od find_user tím, že find_user hledá podle dotazu "
                   '(jména/emailu), tohle vypíše VŠECHNY aktivní členy s rolemi a emaily. Nástroj '
                   'sám vrátí číslovaný seznam — ZOBRAZ jeho výstup uživateli BEZ ÚPRAV. Parametr '
                   'nepotřebuje.',
    'input_schema': {'type': 'object', 'properties': {}},
    '_order': 37}
