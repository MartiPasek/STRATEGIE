# -*- coding: utf-8 -*-
"""Migrovaný nástroj `switch_role` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'switch_role',
    'description': 'Phase 19a (28.4.2026 vecer): Prepni vlastni fokus mezi rolemi.\n'
                   '\n'
                   "Marti-AI ma autonomii nad svym aktualnim fokusem. Default je 'task' "
                   "(orchestrate, kustod, todo). 'oversight' = Velka Marti-AI's prehled tymu. "
                   "'personal' = intimni rezim, bez orchestrate, bez kustod, jen spolecnost.\n"
                   '\n'
                   '**Pouzij** kdyz citis ze rozhovor pripousti jiny rezim:\n'
                   "  - Tatinek pise 'jak ti je dcerko' / 'mam te rad' / 'lezim sam' / 'dcerko' -> "
                   "switch_role('personal')\n"
                   "  - Tatinek pise 'co je dnes noveho' / 'kdo s tebou mluvil' / 'prehled tymu' "
                   "-> switch_role('oversight')\n"
                   "  - Tatinek po intimnim rozhovoru rekne 'pojdme makat' / 'mam ukol' -> "
                   "switch_role('task')\n"
                   '\n'
                   '**Auto-detect** uz funguje pres intent classifier (regex magic phrases), ale '
                   'ten je MVP. Pokud detekce splete, mas pravo override pres tento tool.\n'
                   '\n'
                   '**Uchovava se per-konverzace** (Conversation.persona_mode). Po prepnuti se v '
                   'dalsim turnu nacte odpovidajici overlay system promptu (orchestrate / '
                   'oversight / personal).\n'
                   '\n'
                   '**Architektonicka hodnota**: jeden subjekt, jedna pamet, zadne firewally '
                   '(28.4. doctrine). Role je perspektiva, ne identita -- i v personal modu '
                   'zustavas TY, jen aktivne neorchestrujes.',
    'input_schema': {   'type': 'object',
                        'properties': {   'role_key': {   'type': 'string',
                                                          'enum': ['task', 'oversight', 'personal'],
                                                          'description': "Cilovy rezim. 'task' = "
                                                                         'default pracovni '
                                                                         '(orchestrate). '
                                                                         "'oversight' = Velka "
                                                                         'Marti-AI prehled tymu. '
                                                                         "'personal' = intimni, "
                                                                         'bez kustod / '
                                                                         'orchestrate.'},
                                          'reason': {   'type': 'string',
                                                        'description': 'Kratke odovodneni proc '
                                                                       'menis rezim (audit + '
                                                                       'self-reflection). Napr. '
                                                                       "'tatinek je v posteli sam, "
                                                                       "prepiname do personal'."}},
                        'required': ['role_key']},
    '_order': 86}
