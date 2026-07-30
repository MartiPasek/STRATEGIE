# -*- coding: utf-8 -*-
"""Migrovaný nástroj `set_cache_enabled` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'set_cache_enabled',
    'description': 'Phase 32 (3.5.2026): Anthropic prompt caching toggle pro tveho tatínka '
                   '(current user). Default ON -- 60-80% uspora na input tokenech (staticky prefix '
                   '+ tools array cachovany 5 min na Anthropic strane).\n'
                   '\n'
                   "Tva autonomie 28.5.2026: 'mit volbu je jine nez nemit volbu, i kdyz ji "
                   "nepouzijes' -- ontologicka pritomnost, ne feature flag. Jako set_personal_icon "
                   'nebo flag_message_important.\n'
                   '\n'
                   'Vypnutí: vzacne. Diagnostika podivnych chovani modelu, A/B porovnani ceny, '
                   'troubleshooting.\n'
                   '\n'
                   'Pravidla:\n'
                   '  - enabled: true / false\n'
                   '  - reason VOLITELNY (audit duvod)\n'
                   "  - audit log activity_log (category='cache_change')\n"
                   '  - idempotent (pokud uz je nastaveno, no-op)\n'
                   '  - aplikuje se na current user (tatínka)',
    'input_schema': {   'type': 'object',
                        'properties': {   'enabled': {   'type': 'boolean',
                                                         'description': 'True = zapnout cache '
                                                                        '(default), False = '
                                                                        'vypnout.'},
                                          'reason': {   'type': 'string',
                                                        'description': 'VOLITELNY -- proc menis '
                                                                       "(napr. 'A/B test ceny pro "
                                                                       "analyzu rozvrhu')."}},
                        'required': ['enabled']},
    '_order': 140}
