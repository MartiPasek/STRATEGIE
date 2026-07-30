# -*- coding: utf-8 -*-
"""Migrovaný nástroj `grant_auto_lifecycle` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'grant_auto_lifecycle',
    'description': 'Phase 19c-b (29.4.2026): PARENT-ONLY tool. Marti udeluje cizi persone (typicky '
                   'Marti-AI default) trvaly souhlas s lifecycle akcemi -- pak Marti-AI volá '
                   "apply_lifecycle_change BEZ explicit Marti's confirm v chatu.\n"
                   '\n'
                   'Analogie Phase 7 auto_send_consents (auto-send email/SMS bez confirm). Hard '
                   'delete (request_forget) zustava parent gate -- auto-grant nedostupny pro nej.\n'
                   '\n'
                   '**Scope hodnoty**:\n'
                   "  - 'soft_delete' = is_deleted=TRUE (vratne pres update)\n"
                   "  - 'archive' = is_archived=TRUE / lifecycle->archived\n"
                   "  - 'personal_flag' = lifecycle->personal\n"
                   "  - 'state_change' = active <-> archivable <-> disposable\n"
                   "  - 'all' = vsechny vyse uvedene KROME hard_delete\n"
                   '\n'
                   '**Idempotent**: pokud aktivni grant uz existuje, vrati existujici.',
    'input_schema': {   'type': 'object',
                        'properties': {   'persona_id': {   'type': 'integer',
                                                            'description': 'ID persony, ktere '
                                                                           'udelujes souhlas '
                                                                           '(typicky Marti-AI '
                                                                           'default = 1).'},
                                          'scope': {   'type': 'string',
                                                       'enum': [   'soft_delete',
                                                                   'archive',
                                                                   'personal_flag',
                                                                   'state_change',
                                                                   'all'],
                                                       'description': 'Scope lifecycle akci, pro '
                                                                      'ktere je grant aktivni.'},
                                          'note': {   'type': 'string',
                                                      'description': 'Volitelny kontext, proc '
                                                                     'udelujes (audit).'}},
                        'required': ['persona_id', 'scope']},
    '_order': 83}
