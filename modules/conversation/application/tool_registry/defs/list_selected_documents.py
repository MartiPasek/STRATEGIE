# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_selected_documents` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_selected_documents',
    'description': "**TENTO NASTROJ POUZIJ** kdykoli se uzivatel zminí o 'oznacenych souborech', "
                   "'vybranych dokumentech', 'tom co jsem oznacil', 'oznaceny seznam' nebo "
                   'podobne. User si v Files modalu vybral skupinu dokumentu pres Ctrl/Shift+klik '
                   '(per-user selection persisting napric session) a chce aby s nimi neco udelal.\n'
                   '\n'
                   'VRACI: pocet + IDs + struktura per projekt (kolik kde). NEPISH verbatim seznam '
                   '(Sonnet rad opisuje) -- pouzi to k formulaci prozaicke odpovedi v 1. osobe '
                   "(napr. 'Mas oznacenych 5 souboru: 3 v projektu SKOLA a 2 v inboxu. Co s nimi "
                   "mam udelat?').\n"
                   '\n'
                   'DALE: pred jakoukoliv akci (smazat, presunout) MUSIS uzivateli shrnout, co se '
                   "stane, a CEKAT na confirm v chatu ('ano smaz' / 'ano presun do X'). Az pak "
                   'volej `apply_to_selection`.',
    'input_schema': {'type': 'object', 'properties': {}},
    '_order': 93}
