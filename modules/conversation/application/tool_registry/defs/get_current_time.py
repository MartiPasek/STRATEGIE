# -*- coding: utf-8 -*-
"""Migrovaný nástroj `get_current_time` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'get_current_time',
    'description': 'Phase 20b (29.4.2026): Vrati aktualni cas v zadane timezone. POZNAMKA: '
                   'aktualni cas v Europe/Prague vidis jiz v system promptu v sekci [AKTUÁLNÍ ČAS] '
                   "-- pro běžné dotazy 'kolik je hodin' tento tool nepotřebuješ. Volej ho jen "
                   "pro: (a) explicitní casove vypocty ('kolik bude za 3 hodiny'), (b) jine "
                   'timezone nez Europe/Prague, (c) presny cas s sekundami (system prompt '
                   'zaokrouhluje na minuty).',
    'input_schema': {   'type': 'object',
                        'properties': {   'timezone': {   'type': 'string',
                                                          'description': 'IANA timezone '
                                                                         'identifier. Default '
                                                                         "'Europe/Prague'. Jine "
                                                                         "moznosti: 'UTC', "
                                                                         "'America/New_York', atd.",
                                                          'default': 'Europe/Prague'}},
                        'required': []},
    '_order': 109}
