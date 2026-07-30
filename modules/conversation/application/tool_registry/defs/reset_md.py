# -*- coding: utf-8 -*-
"""Migrovaný nástroj `reset_md` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'reset_md',
    'description': 'Phase 24-D: HARD reset content md_document na default template (version=1). '
                   'DESTRUKTIVNI -- content_md se prepise. Vyzaduje vyslovny souhlas Marti-Pasek '
                   "(parent). Pouziti pri velkem omylu Marti-AI ('drz chybny obraz po dlouhe "
                   "konverzaci'). Pre-reset content je v audit trail md_lifecycle_history.",
    'input_schema': {   'type': 'object',
                        'properties': {   'md_id': {   'type': 'integer',
                                                       'description': 'ID md_document k resetu.'},
                                          'reason': {   'type': 'string',
                                                        'description': 'Duvod resetu (povinny -- '
                                                                       'destruktivni akce).'}},
                        'required': ['md_id', 'reason']},
    '_order': 130}
