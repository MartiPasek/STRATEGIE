# -*- coding: utf-8 -*-
"""Migrovaný nástroj `hledej_ve_znalostech` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'hledej_ve_znalostech',
    'description': 'Vyhledá ve SDÍLENÉ ZNALOSTNÍ BÁZI firmy (RAG) — firemní a doménové know-how: '
                   'obchod, cenotvorba, kalkulace rozváděčů, komponenty a výrobci, procesy, '
                   'směrnice a jejich přílohy. POUŽIJ reflexivně vždy, když se řeší cokoli o '
                   'firmě, zakázkách, produktech, cenách, komponentách nebo postupech a ty odpověď '
                   'nemáš v kontextu. Nedrž firemní znalosti v hlavě — nemáš je; vytáhni si z báze '
                   'JEN to, co k dané věci potřebuješ (rychle, na vyžádání). Vrátí pár '
                   'nejrelevantnějších záznamů (název + úryvek). Pro orientaci ve vlastních '
                   "AI-znalostech sítě zadej ai_only=true (řada 'AI', vč. MAPY firmy).",
    'input_schema': {   'type': 'object',
                        'properties': {   'dotaz': {   'type': 'string',
                                                       'description': 'Klíčová slova / téma (např. '
                                                                      "'VKM materiál', 'ISIMAT', "
                                                                      "'cenotvorba', 'motorový "
                                                                      "jistič 3RV')."},
                                          'ai_only': {   'type': 'boolean',
                                                         'description': 'true = jen řada AI '
                                                                        '(orientační AI znalosti + '
                                                                        'MAPA firmy). Default '
                                                                        'false = i firemní '
                                                                        'směrnice.',
                                                         'default': False}},
                        'required': ['dotaz']},
    '_order': 16}
