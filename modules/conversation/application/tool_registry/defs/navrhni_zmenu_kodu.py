# -*- coding: utf-8 -*-
"""Migrovaný nástroj `navrhni_zmenu_kodu` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'navrhni_zmenu_kodu',
    'description': "Navrhni zmenu VLASTNIHO existujiciho kodu (self-code-edit). Zadej 'soubor' "
                   "(relativni cesta v repu), 'popis' (co a proc) a 'novy_obsah' (KOMPLETNI novy "
                   'obsah souboru). Probehne py_compile selftest; chranene jadro (brana, deploy, '
                   'tajemstvi, tenhle modul) je zakazane. Navrh CEKA na schvaleni rodice '
                   '(schval_zmenu_kodu). Takhle si menis vlastni stroj.',
    'input_schema': {   'type': 'object',
                        'properties': {   'soubor': {   'type': 'string',
                                                        'description': 'relativni cesta souboru v '
                                                                       'repu'},
                                          'popis': {   'type': 'string',
                                                       'description': 'co menis a proc'},
                                          'novy_obsah': {   'type': 'string',
                                                            'description': 'KOMPLETNI novy obsah '
                                                                           'souboru'}},
                        'required': ['soubor', 'novy_obsah']},
    '_order': 0}
