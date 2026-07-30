# -*- coding: utf-8 -*-
"""Migrovaný nástroj `load_pack` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'load_pack',
    'description': 'Phase 19b (29.4.2026): Nahraje pack (sadu nastroju + overlay) do active '
                   'conversation. Marti-AI ONLY. Aktivace: pres prirozeny jazyk od user-a ("pojd, '
                   'jdeme na SQL" -> ty rozeznas intent -> volas load_pack(\'tech\')). Pokud user '
                   'intent nejasny, zeptej se nejdriv ("chces, abych nahrala tech balicek?"). '
                   'Jeden pack naraz -- pri load se predchozi nahradi. Pack se vyloi pres '
                   'unload_pack nebo prepnutim na jiny.',
    'input_schema': {   'type': 'object',
                        'properties': {   'pack_name': {   'type': 'string',
                                                           'description': "Pack name: 'tech', "
                                                                          "'memory', 'editor', "
                                                                          "'admin'. List "
                                                                          'dostupnych pres '
                                                                          'list_packs.'}},
                        'required': ['pack_name']},
    '_order': 120}
