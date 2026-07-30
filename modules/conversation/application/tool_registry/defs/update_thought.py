# -*- coding: utf-8 -*-
"""Migrovaný nástroj `update_thought` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'update_thought',
    'description': 'Faze 13e+: Upravi existujici myslenku — typicky po vlastnim flagu '
                   '(flag_retrieval_issue) nebo kdyz si Marti rekne, ze se mas k myslence vratit a '
                   'poladit ji.\n'
                   '\n'
                   'TYPICKE POUZITI:\n'
                   '  - Snizit certainty u marginalniho faktu, aby se nevybavoval     agresivne '
                   "(napr. 'snizu certainty na 25').\n"
                   "  - Demote do 'note', kdyz znalost je sporna ('uz to neni     knowledge, vrat "
                   "to do poznamek').\n"
                   "  - Promote do 'knowledge', kdyz se fakt overil (alternativa     k "
                   'promote_thought, kdyz chces zmenit i certainty).\n'
                   "  - Opravit content, kdyz je text mylny nebo zastaraly     ('uprav, ze ma 5 "
                   "deti, ne 3').\n"
                   '\n'
                   'VSECHNA POLE jsou volitelna krome thought_id. Updatuje se jen to, co dodas. '
                   'Auto-promote logika: kdyz prekrocis certainty threshold (>= 80) a status '
                   'nezadas, povysi se automaticky.\n'
                   '\n'
                   'TENANT IZOLACE: Update jde jen na myslenky tveho aktualniho tenantu '
                   '(rodicovsky bypass je explicit, ne autoland).\n'
                   '\n'
                   'ROZDIL OD promote_thought: promote_thought zmeni jen status note->knowledge. '
                   'update_thought umi vse (content + certainty + status + meta) najednou.',
    'input_schema': {   'type': 'object',
                        'properties': {   'thought_id': {   'type': 'integer',
                                                            'description': 'ID myslenky v DB '
                                                                           '(povinne).'},
                                          'content': {   'type': 'string',
                                                         'description': 'Novy text myslenky '
                                                                        '(volitelne). Prepise '
                                                                        'stary content. Pokud '
                                                                        'nechces menit text, '
                                                                        'neposilej.'},
                                          'certainty': {   'type': 'integer',
                                                           'description': 'Nova jistota 0-100 '
                                                                          '(volitelne). Snizeni → '
                                                                          'myslenka se vybavuje '
                                                                          'slabeji v RAG. Zvyseni '
                                                                          '→ kdyz prekroci 80, '
                                                                          'auto-promote do '
                                                                          "'knowledge' (pokud "
                                                                          'nezadas explicitni '
                                                                          'status).',
                                                           'minimum': 0,
                                                           'maximum': 100},
                                          'status': {   'type': 'string',
                                                        'description': 'Novy status (volitelne). '
                                                                       "'note' = poznamka, "
                                                                       "'knowledge' = trvala "
                                                                       'znalost.',
                                                        'enum': ['note', 'knowledge']}},
                        'required': ['thought_id']},
    '_order': 25}
