# -*- coding: utf-8 -*-
"""Migrovaný nástroj `g2007_hledej` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'g2007_hledej',
    'description': 'Sémantické hledání v G2007 — NOSNÉ znalostní bázi STRATEGIE (čisté, '
                   'kurátorované know-how bez balastu: mzdy, účetnictví, ISO 27001, docházka, '
                   'kalkulace rozváděčů, systém G2007, Marti-AI, nabídky, TISAX). Na rozdíl od '
                   '`hledej_ve_znalostech` (obecná RAG paměť sítě) je G2007 kanonická, schválená '
                   'báze — použij ji, když potřebuješ ověřený postup, runbook nebo pravidlo (např. '
                   "'jak uzavřít mzdy a zaúčtovat', 'co vyžaduje středisko', 'ISO plán "
                   "certifikace'). Vrátí nejrelevantnější RŮZNÉ znalosti (nadpis + kód + shoda + "
                   'úryvek). Volitelně zúžíš na jednu oblast.',
    'input_schema': {   'type': 'object',
                        'properties': {   'dotaz': {   'type': 'string',
                                                       'description': 'Otázka nebo téma přirozeným '
                                                                      "jazykem (např. 'uzávěrka "
                                                                      "mezd středisko', 'DR plán "
                                                                      "RTO RPO')."},
                                          'oblast': {   'type': 'string',
                                                        'description': 'Volitelně: kód oblasti pro '
                                                                       'zúžení (mzdy, ucetnictvi, '
                                                                       'iso27001, dochazka, '
                                                                       'kalkulace-rozvadecu, '
                                                                       'system-g2007, marti-ai, '
                                                                       'nabidky, tisax).'},
                                          'k': {   'type': 'integer',
                                                   'description': 'Volitelně: kolik znalostí '
                                                                  'vrátit (1–12, default 6).',
                                                   'default': 6}},
                        'required': ['dotaz']},
    '_order': 17}
