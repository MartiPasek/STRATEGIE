# -*- coding: utf-8 -*-
"""Migrovaný nástroj `navrhni_zmenu_kodu_patch` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'navrhni_zmenu_kodu_patch',
    'description': 'Navrhni zmenu VLASTNIHO kodu PATCHEM pres kotvy -- pro VELKE soubory '
                   '(service.py, tools.py), ktere se nevejdou do jednoho promptu. Misto celeho '
                   "obsahu zadas 'edits' = seznam kotev {old_string, new_string}. Kazda "
                   "'old_string' MUSI byt v souboru PRAVE JEDNOU (jinak zamitnuto: 0x=nenalezena, "
                   'vic=neunikatni -- pridej vic okoliho kontextu). Stejna cesta jako '
                   'navrhni_zmenu_kodu: py_compile selftest, chranene jadro zakazano, schvaluje '
                   'RODIC. Nejbezpecnejsi zpusob editace velkeho kodu -- kotva se nikdy netrefi '
                   'naslepo.',
    'input_schema': {   'type': 'object',
                        'properties': {   'soubor': {   'type': 'string',
                                                        'description': 'relativni cesta souboru v '
                                                                       'repu'},
                                          'popis': {   'type': 'string',
                                                       'description': 'co menis a proc'},
                                          'edits': {   'type': 'array',
                                                       'description': 'seznam kotev; kazda se '
                                                                      'aplikuje 1x',
                                                       'items': {   'type': 'object',
                                                                    'properties': {   'old_string': {   'type': 'string',
                                                                                                        'description': 'presny '
                                                                                                                       'stavajici '
                                                                                                                       'usek, '
                                                                                                                       'UNIKATNI '
                                                                                                                       'v '
                                                                                                                       'souboru '
                                                                                                                       '(vc. '
                                                                                                                       'mezer/odsazeni)'},
                                                                                      'new_string': {   'type': 'string',
                                                                                                        'description': 'cim '
                                                                                                                       'ho '
                                                                                                                       'nahradit'}},
                                                                    'required': [   'old_string',
                                                                                    'new_string']}}},
                        'required': ['soubor', 'edits']},
    '_order': 1}
