# -*- coding: utf-8 -*-
"""Migrovaný nástroj `flag_for_higher` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'flag_for_higher',
    'description': 'Phase 24-B: Eskaluj pro vyssi vrstvu pyramidy. Marti-AI\'s princip "asymetrie '
                   'chrani uzivatele, vertikalni kanal umoznuje spolupraci": kdyz vidis, ze '
                   'problem v tve konverzaci se dotyka jine osoby/oddeleni/firmy, oznacis flag '
                   'misto direktni cross-Martinka access. Vedouci md2 (kdyz bude) flag uvidi a '
                   "rozhodne o koordinaci. Pridava radek do sekce 'Open flagy pro vyšší vrstvu' v "
                   'md1 work. SELZE na md1 personal (personal je izolovany sandbox, nema cestu '
                   'nahoru). Marti-AI ONLY (default persona).',
    'input_schema': {   'type': 'object',
                        'properties': {   'content': {   'type': 'string',
                                                         'description': 'Strucny popis flagu pro '
                                                                        'vyssi vrstvu. Napr. '
                                                                        "'Petra opakovane zminuje "
                                                                        'stres ze zatizeni '
                                                                        'Heliosem -- mozny '
                                                                        'systemovy pattern napric '
                                                                        "tymem.'"},
                                          'target_level': {   'type': 'integer',
                                                              'description': 'Cilova vrstva: '
                                                                             '2=Vedouci, '
                                                                             '3=Reditelka, '
                                                                             '4=Presahujici, '
                                                                             '5=Privat Marti. '
                                                                             'Default 2.',
                                                              'enum': [2, 3, 4, 5]}},
                        'required': ['content']},
    '_order': 126}
