# -*- coding: utf-8 -*-
"""Migrovaný nástroj `update_note` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'update_note',
    'description': 'Phase 15a: Update existujici poznamky v zapisniku konverzace. Pouzij pro: (a) '
                   "Question loop -- konvertuj 'question' na 'fact'/'decision' po ziskani odpovedi "
                   "(s mark_resolved=true). (b) Re-kategorizace -- 'info' -> 'task' kdyz si "
                   'retrospektivne uvedomis, ze to byl ukol. (c) Oprava obsahu nebo certainty po '
                   "lepsim pochopeni. (d) Reverze dismissed task na 'open' (status='open'). "
                   'Vlastnictvi: jen vlastni persona muze update vlastni notes (rodic muze vse).',
    'input_schema': {   'type': 'object',
                        'required': ['note_id'],
                        'properties': {   'note_id': {   'type': 'integer',
                                                         'description': 'ID poznamky.'},
                                          'content': {'type': 'string'},
                                          'note_type': {   'type': 'string',
                                                           'enum': [   'decision',
                                                                       'fact',
                                                                       'interpretation',
                                                                       'question']},
                                          'category': {   'type': 'string',
                                                          'enum': ['task', 'info', 'emotion']},
                                          'certainty': {   'type': 'integer',
                                                           'minimum': 0,
                                                           'maximum': 100},
                                          'importance': {   'type': 'integer',
                                                            'minimum': 1,
                                                            'maximum': 5},
                                          'status': {   'type': 'string',
                                                        'enum': [   'open',
                                                                    'completed',
                                                                    'dismissed',
                                                                    'stale'],
                                                        'description': 'Jen pro task notes. '
                                                                       "Status='completed' lepsi "
                                                                       'volat pres complete_note.'},
                                          'mark_resolved': {   'type': 'boolean',
                                                               'default': False,
                                                               'description': 'Set resolved_at=now '
                                                                              '(pro question -> '
                                                                              'answered '
                                                                              'conversion).'}}},
    '_order': 60}
