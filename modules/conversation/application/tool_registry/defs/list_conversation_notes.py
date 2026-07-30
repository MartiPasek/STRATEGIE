# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_conversation_notes` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_conversation_notes',
    'description': 'Phase 15a: Vypis poznamky v zapisniku TETO konverzace. Vetsinou to '
                   'nepotrebujes -- composer ti je vzdy injectuje do system promptu v sekci '
                   '[ZAPISNICEK pro konverzaci #X]. Pouzij jen kdyz potrebujes kompletni vypis '
                   '(vcetne archived) nebo specificky filter.',
    'input_schema': {   'type': 'object',
                        'properties': {   'filter_category': {   'type': 'string',
                                                                 'enum': [   'task',
                                                                             'info',
                                                                             'emotion']},
                                          'filter_status': {   'type': 'string',
                                                               'enum': [   'open',
                                                                           'completed',
                                                                           'dismissed',
                                                                           'stale']},
                                          'only_open_tasks': {   'type': 'boolean',
                                                                 'default': False,
                                                                 'description': 'Shortcut: jen '
                                                                                'task notes s '
                                                                                "status='open'."},
                                          'include_archived': {   'type': 'boolean',
                                                                  'default': False}}},
    '_order': 63}
