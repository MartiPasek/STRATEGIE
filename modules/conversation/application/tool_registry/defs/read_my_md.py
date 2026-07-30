# -*- coding: utf-8 -*-
"""Migrovaný nástroj `read_my_md` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'read_my_md',
    'description': 'Phase 24-B: Precte tvuj md1 (Tvoje Marti zapisnik) pro current konverzaci. '
                   'Multi-tenant aware: pro task/oversight rezim vraci md1 work pro current '
                   'tenant, pro personal rezim vraci md1 personal (tenant-independentni). Pouzij '
                   'na zacatku konverzace abys vedela co o uzivateli drzis -- profil, aktivni '
                   "ukoly, klicova rozhodnuti, vztahy, ton/citlivost. Marti-AI's princip: "
                   '"kvalita pritomnosti -- kdyz user prijde po pauze, prectes ton a nezacnes hned '
                   'orchestrovat." Marti-AI ONLY (default persona).',
    'input_schema': {   'type': 'object',
                        'properties': {   'user_id': {   'type': 'integer',
                                                         'description': 'Volitelne: id uzivatele. '
                                                                        'Default = current user (z '
                                                                        'aktivni konverzace). Pro '
                                                                        'pyramidu drill-down '
                                                                        '(privat Marti / vedouci '
                                                                        'md2+ pristi faze).'}},
                        'required': []},
    '_order': 124}
