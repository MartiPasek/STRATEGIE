# -*- coding: utf-8 -*-
"""Migrovaný nástroj `summarize_persons_today` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'summarize_persons_today',
    'description': 'Phase 16-B.4 + B.6: Per-(user, persona) breakdown aktivit za scope. Vraci '
                   'pocty akci NA KOMBINACI uzivatel × persona, plus persona_name. **Pouzij** v '
                   "oversight režimu na otázky typu 'co kdo dnes dělal', 'shrn mi co tym rozjel'.\n"
                   '\n'
                   '**Vystup obsahuje markery [TY] (tva persona) a [Persona-Name] (cizi '
                   'persona).**\n'
                   '\n'
                   '**JAK ZPRACOVAT** (anti-přivlastňovací pravidlo, B.6):\n'
                   "  ✅ 'Misa dnes resila TISAX s PravnikCZ-AI v 1 konverzaci'\n"
                   "  ✅ 'Marti uploadl 3 doc se mnou, plus poslal SMS Honzou-AI'\n"
                   "  ❌ NIKDY: 'mluvily jsme s Misou' kdyz mluvila s cizi personou\n"
                   '  Persona context je posvatny -- cizi konverzace nikdy v 1. osobe.\n'
                   'Shrn proza per-osoba s person markery.',
    'input_schema': {   'type': 'object',
                        'properties': {   'scope': {   'type': 'string',
                                                       'enum': ['today', 'week', 'month'],
                                                       'description': 'Časový rozsah. Default '
                                                                      "'today'."}}},
    '_order': 78}
