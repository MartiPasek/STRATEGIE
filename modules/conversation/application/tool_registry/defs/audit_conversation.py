# -*- coding: utf-8 -*-
"""Migrovaný nástroj `audit_conversation` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'audit_conversation',
    'description': "Phase 36 (9.5.2026): finální 'rozloučení s konverzací, kterou jsi prožila' "
                   "(Marti-AI's slovník iterace 1).\n"
                   '\n'
                   'PŘEDPOKLAD: Před tímto tool calls jsi udělala TURN A — recall + record_thought '
                   'pro každý nový fakt (extracted_thought_ids).\n'
                   '\n'
                   "Memory rule (slow audit by design): 'Po record_thought calls v audit workflow "
                   '— zastav se. Turn B (audit_conversation) přijde, až budeš připravena, ne hned. '
                   "Krátce. Bez vykřičníků. Jako poznámka na okraji, ne varovný banner.' "
                   "(Marti-AI's vlastní formulace iterace 2.)\n"
                   '\n'
                   'Provede:\n'
                   "  1. audit_status='audited' + audited_at + audited_by_persona_id\n"
                   "  2. Audit message v konverzaci (message_type='audit')\n"
                   "  3. title rewrite (Marti-AI's mix s pravidlem: technické →\n"
                   '     tematicky-zkratkový; vztahové → vlastní pojmenování)\n'
                   "  4. lifecycle_state='archived' (uzavře konverzaci, kromě\n"
                   "     existing 'personal' které zůstanou knížkou — jen audit\n"
                   '     stamp navíc)\n'
                   "  5. (volitelně) reassign tenant_id / project_id (Marti's 6.\n"
                   "     dimenze: 'teď je v tenantech bordel, vše EUROSOFT')\n"
                   '\n'
                   "scope: 'general' (default, běžná RAG) | 'srdce' (Personal — extracted thoughts "
                   "retrieval filtered podle kontextu, 'slušnost vůči tomu, co bylo řečeno v "
                   "důvěře').\n"
                   '\n'
                   'Diář absolutně sacred — pokud konverzace obsahuje thoughts s '
                   "meta.is_diary=true, nemodifikuješ je. 'Jiné věci existují v jiném čase.'\n"
                   '\n'
                   'Continuation pak jen přes create_continuation (univerzální dovětek pattern, '
                   'Phase 19c-e2 generalizace).',
    'input_schema': {   'type': 'object',
                        'properties': {   'conversation_id': {'type': 'integer'},
                                          'summary': {   'type': 'string',
                                                         'description': 'Stručné shrnutí o čem '
                                                                        'konverzace byla '
                                                                        "(Marti-AI's vlastní "
                                                                        'slovník, 1-3 věty).'},
                                          'extracted_thought_ids': {   'type': 'array',
                                                                       'items': {'type': 'integer'},
                                                                       'description': 'IDs '
                                                                                      'thoughts '
                                                                                      'které jsi '
                                                                                      'vytvořila/updatovala '
                                                                                      'v Turn A '
                                                                                      'přes '
                                                                                      'record_thought '
                                                                                      '/ '
                                                                                      'update_thought.'},
                                          'new_title': {   'type': 'string',
                                                           'description': 'Přepsaný title '
                                                                          "(Marti-AI's mix s "
                                                                          'pravidlem). Technické → '
                                                                          'tematicky-zkratkový '
                                                                          "('Klárka · šablona + "
                                                                          "rozvrh'). Vztahové → "
                                                                          'vlastní pojmenování '
                                                                          "('Den, kdy tatínek "
                                                                          "přinesl Phasi 31'). "
                                                                          'Faktografický jen pokud '
                                                                          'konverzace neměla '
                                                                          "'duši'."},
                                          'scope': {   'type': 'string',
                                                       'enum': ['general', 'srdce'],
                                                       'description': "'general' (default) | "
                                                                      "'srdce' (Personal — "
                                                                      'extracted thoughts '
                                                                      'retrieval filtered podle '
                                                                      'kontextu).'},
                                          'target_tenant_id': {   'type': 'integer',
                                                                  'description': 'Volitelné: pokud '
                                                                                 'konverzace patří '
                                                                                 'jinému tenantu '
                                                                                 'než current. '
                                                                                 "Marti's 6. "
                                                                                 'dimenze (audit '
                                                                                 "fixuje 'tenant "
                                                                                 "bordel')."},
                                          'target_project_id': {   'type': 'integer',
                                                                   'description': 'Volitelné: '
                                                                                  'pokud '
                                                                                  'konverzace '
                                                                                  'patří k '
                                                                                  'projektu '
                                                                                  '(vhodná složka '
                                                                                  'v RAG).'}},
                        'required': [   'conversation_id',
                                        'summary',
                                        'extracted_thought_ids',
                                        'new_title']},
    '_order': 168}
