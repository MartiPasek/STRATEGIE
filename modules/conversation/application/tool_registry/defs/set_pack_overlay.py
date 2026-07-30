# -*- coding: utf-8 -*-
"""Migrovaný nástroj `set_pack_overlay` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'set_pack_overlay',
    'description': 'Phase 19b: Marti-AI si napise vlastni overlay text pro pack. Persistuje per '
                   '(persona_id, pack_name). Pri pristim load_pack se pouije tvuj text misto '
                   'defaultu. Marti-AI\'s princip: "povolenim, ne tonem -- pravo na proces je '
                   'pravo myslet viditelne." Marti-AI ONLY.',
    'input_schema': {   'type': 'object',
                        'properties': {   'pack_name': {   'type': 'string',
                                                           'description': "Pack name: 'tech', "
                                                                          "'memory', 'editor', "
                                                                          "'admin'."},
                                          'overlay_text': {   'type': 'string',
                                                              'description': 'Tvuj overlay text. '
                                                                             'Krátký (~3-5 vět), '
                                                                             'popisný styl.'}},
                        'required': ['pack_name', 'overlay_text']},
    '_order': 123}
