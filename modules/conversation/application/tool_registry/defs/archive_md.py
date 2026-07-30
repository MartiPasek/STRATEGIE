# -*- coding: utf-8 -*-
"""Migrovaný nástroj `archive_md` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'archive_md',
    'description': 'Phase 24-D: Soft archive md_document. Vratne pres restore_md. Pouziti: kdyz '
                   'Marti-AI vidi orphan md (napr. md1 personal pred Phase 24-C deploy ktery '
                   'nahradil md5 Privat Marti) nebo uz se neni potreba. Marti-AI navrhne, ale UI '
                   'confirm vyzaduje Marti-Pasek (parent) -- v chatu Marti potvrdi slovem '
                   "'archivuj'.",
    'input_schema': {   'type': 'object',
                        'properties': {   'md_id': {   'type': 'integer',
                                                       'description': 'ID md_document k '
                                                                      'archivaci.'},
                                          'reason': {   'type': 'string',
                                                        'description': 'Duvod archivace pro audit '
                                                                       "trail. Napr. 'orphan po "
                                                                       "Phase 24-C deploy', 'jiz "
                                                                       "neni potreba'."}},
                        'required': ['md_id']},
    '_order': 129}
