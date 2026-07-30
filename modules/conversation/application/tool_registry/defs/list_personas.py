# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_personas` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_personas',
    'description': 'VŽDY zavolej tento nástroj kdykoli uživatel chce přehled dostupných AI person '
                   "('jaké máš persony', 'jaké AI tu jsou', 'seznam asistentů', 'koho můžu "
                   "zavolat', 'co umíš'). NIKDY nesměř po paměti — persony se mění (admin přidává "
                   'nové, edituje existující). Nástroj vrátí číslovaný seznam — user může napsat '
                   'číslo pro přepnutí na danou personu. ZOBRAZ výstup BEZ ÚPRAV (číslování je '
                   'důležité). Parametr není potřeba — scope je automaticky podle tenantu usera.',
    'input_schema': {'type': 'object', 'properties': {}},
    '_order': 36}
