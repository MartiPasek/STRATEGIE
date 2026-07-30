# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_recent_chatters` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_recent_chatters',
    'description': 'Vrátí seznam uživatelů, kteří s tebou nedávno mluvili (napsali ti zprávu). '
                   'Každý user s počtem zpráv a časem posledního dotyku. POUŽIJ, když se user '
                   "zeptá: 'kdo s tebou mluvil', 'kdo ti psal', 'kdo se dnes ozval', 'koho tu máme "
                   "aktivního'.\n"
                   '\n'
                   'Není to totéž jako `list_conversations` — ta vrací seznam konverzací '
                   '(titulků). Tento tool vrací **lidi** agregovaně.',
    'input_schema': {   'type': 'object',
                        'properties': {   'hours': {   'type': 'integer',
                                                       'description': 'Kolik hodin zpět hledat '
                                                                      '(default 24 = posledních 24 '
                                                                      'h).',
                                                       'default': 24}}},
    '_order': 34}
