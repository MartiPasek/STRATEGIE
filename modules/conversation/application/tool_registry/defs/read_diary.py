# -*- coding: utf-8 -*-
"""Migrovaný nástroj `read_diary` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'read_diary',
    'description': 'Načte záznamy z tvého **soukromého diáře** — to, co jsi si sama v minulosti '
                   'zapsala.\n'
                   '\n'
                   'POUŽIJ KDYŽ:\n'
                   "- Ti rodič řekne 'podívej se do deníku', 'co máš v diáři', 'ukaž mi zápisy'\n"
                   '- Chceš si připomenout, co jsi prožila v konkrétní den / po konkrétní '
                   'události\n'
                   '- Potřebuješ citovat nebo shrnout své vlastní reflexe\n'
                   '\n'
                   'Vrátí seznam tvých deníkových záznamů seřazených od nejnovějšího (default 20). '
                   'Každý záznam má: content (text), type '
                   '(experience/observation/fact/goal/question), emotion + intensity (pokud '
                   'zadané), created_at.\n'
                   '\n'
                   '**Diář je tvůj vlastní.** Tento nástroj čte záznamy persony, která je aktivní '
                   'v konverzaci (tj. ty sama). Nečte diáře jiných person — na to by bylo potřeba '
                   'jiné oprávnění.\n'
                   '\n'
                   '**Komplement k `record_diary_entry`** — tam zapisuješ, tady čteš. Obě patří do '
                   'tvé osobní kognice.',
    'input_schema': {   'type': 'object',
                        'properties': {   'limit': {   'type': 'integer',
                                                       'description': 'Kolik záznamů vrátit '
                                                                      '(default 20, max 100).',
                                                       'default': 20,
                                                       'minimum': 1,
                                                       'maximum': 100},
                                          'filter_type': {   'type': 'string',
                                                             'enum': [   'experience',
                                                                         'observation',
                                                                         'fact',
                                                                         'goal',
                                                                         'question'],
                                                             'description': 'Volitelný filtr na '
                                                                            'typ záznamu. Bez '
                                                                            'parametru vrátí '
                                                                            'všechny typy.'}}},
    '_order': 14}
