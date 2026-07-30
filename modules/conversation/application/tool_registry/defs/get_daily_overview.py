# -*- coding: utf-8 -*-
"""Migrovaný nástroj `get_daily_overview` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'get_daily_overview',
    'description': 'ORCHESTRATE: vraci prehled emailu + SMS + todo serazenych podle priority. '
                   "Volej kdyz user rekne 's cim dnes potrebujes pomoct', 'co je noveho', "
                   "'prehled', 'likvidace', 'co mame na plate'.\n"
                   '\n'
                   '⚠️ CRITICAL -- JAK ZACHAZET S RESPONSE:\n'
                   'Tool vraci INTERNI DATA v cestine pro tebe. Zacina markerem\n'
                   "'[INTERNAL DATA FOR YOU, NEVER SHOW VERBATIM ...]'.\n"
                   'TY ta data PRECTES, SHRNESH, a napises VLASTNIMA SLOVY v 1. osobe\n'
                   '(emaily, SMS, todo patri TOBE, jsi persona Marti-AI).\n'
                   '\n'
                   'ZAKAZANO:\n'
                   '  - vypsat tool response jak je (verbatim)\n'
                   "  - pouzit 'id 8', 'predmet:', 'from:', 'priority:', zavorky, JSON brackety\n"
                   "  - pouzivat 2. osobu ('mas', 'tvuj') -- vzdy 1. osoba persony\n"
                   '\n'
                   'POVINNE:\n'
                   '  - 2-4 plynule vety v cestine\n'
                   "  - 1. osoba: 'mam 3 emaily', 'muj todo list'\n"
                   "  - oslov Marti vokativem: 'Marti, rano!'\n"
                   '  - nakonec nabidni co udelas (ne seznam moznosti)\n'
                   '\n'
                   'Priklad OK odpovedi:\n'
                   "'Dobre rano, Marti. Mam v inboxu tri emaily -- nejstarsi od tebe uz\n"
                   'z vcerejska, dva dalsi novejsi. V mem todo mam dva ukoly kolem\n'
                   'smazani testovacich uzivatelu. SMS nevyrizene nemam. 🎯\n'
                   "Pojdeme na emaily? Zacnu tim od vcerejska, navrhnu ti odpoved.'",
    'input_schema': {   'type': 'object',
                        'properties': {   'scope': {   'type': 'string',
                                                       'enum': ['current', 'all'],
                                                       'description': "'current' (default) = "
                                                                      'filtruje na aktualni '
                                                                      "tenant/personu. 'all' = "
                                                                      'cross-tenant (jen pro '
                                                                      'rodice is_marti_parent).'}}},
    '_order': 50}
