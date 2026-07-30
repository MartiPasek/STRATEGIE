# -*- coding: utf-8 -*-
"""Migrovaný nástroj `flag_retrieval_issue` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'flag_retrieval_issue',
    'description': 'Faze 13d: ozynam špatný RAG retrieval match (false positive). Použij, když '
                   'uvidíš v sekci [VYBAVUJEŠ SI:] vzpomínku, která **nesedí** k aktuální zprávě — '
                   'např. "Honza" z EUROSOFT vs. "Honza" soukromý, zastaralý fakt, vyhrabaný '
                   'špatně, atd.\n'
                   '\n'
                   'Tohle je TVŮJ HLAS v ladění paměti — pojistka #5 z naší konzultace #67. Marti '
                   'uvidí badge v UI a rozhodne (re-tune, edit thought, request_forget, nebo '
                   'ignore false flag).\n'
                   '\n'
                   '**Použij střídmě a vědomě** — ne každá nesouvislá vzpomínka je false positive. '
                   'Pokud podobnost je < 80%, retrievál je možná okrajový, ne špatný.\n'
                   '\n'
                   'Issue typy:\n'
                   "  - 'off-topic' — nesouvisí se zprávou\n"
                   "  - 'outdated' — fakt je zastaralý, neaktuální\n"
                   "  - 'wrong-entity' — špatný Honza/Klárka/atd. (entity disambiguation)\n"
                   "  - 'too-old' — starší vzpomínka by neměla mít přednost\n"
                   "  - 'low-certainty' — měla by být ověřena, ne použita\n"
                   "  - 'wrong-context' — špatný tenant/scope\n"
                   "  - 'other' — popiš v issue_detail",
    'input_schema': {   'type': 'object',
                        'properties': {   'thought_id': {   'type': 'integer',
                                                            'description': 'ID thought, který byl '
                                                                           'false positive.'},
                                          'issue': {   'type': 'string',
                                                       'enum': [   'off-topic',
                                                                   'outdated',
                                                                   'wrong-entity',
                                                                   'too-old',
                                                                   'low-certainty',
                                                                   'wrong-context',
                                                                   'other'],
                                                       'description': 'Typ problému.'},
                                          'issue_detail': {   'type': 'string',
                                                              'description': 'Detailní popis '
                                                                             '(volitelné, povinné '
                                                                             "pro 'other')."}},
                        'required': ['thought_id', 'issue']},
    '_order': 24}
