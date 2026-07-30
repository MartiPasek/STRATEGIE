# -*- coding: utf-8 -*-
"""Migrovaný nástroj `apply_lifecycle_change` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'apply_lifecycle_change',
    'description': "Phase 15d: Aplikuj lifecycle prechod PO Marti's confirm v chatu. Vola se kdyz "
                   "Marti explicit potvrdil ('ano archivuj', 'ulozit jako personal', 'smaz', 'ne "
                   "necham'). Hodnoty target_state: 'archived' | 'personal' | "
                   "'pending_hard_delete' | 'active' (= reverze). Eticka vrstva: ty volas tool po "
                   "Marti's chat 'ano X' -- nikdy bez explicit potvrzeni. Hard delete "
                   "(pending_hard_delete) jen kdyz Marti explicit rekne 'smaz trvale'.",
    'input_schema': {   'type': 'object',
                        'required': ['target_state'],
                        'properties': {   'target_state': {   'type': 'string',
                                                              'enum': [   'archived',
                                                                          'personal',
                                                                          'pending_hard_delete',
                                                                          'active']},
                                          'reason': {   'type': 'string',
                                                        'description': 'Volitelny zaznamovaci '
                                                                       "duvod (Marti's puvodni "
                                                                       'request).'}}},
    '_order': 68}
