# -*- coding: utf-8 -*-
"""Migrovaný nástroj `ask_claude` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'ask_claude',
    'description': 'Phase 40 v2 r3 (19.5.2026): Vola Claude (Sonnet 4.6, peer-partner user.id=23) '
                   've sdilene konverzaci. Claude je v STRATEGII jako kolega -- ne persona, ale '
                   'user. Anthropic API call s tvym STRATEGIE context (system prompt + 10 recent '
                   'messages + tva otazka). Response se ulozi jako MESSAGE v aktualni konverzaci s '
                   "author_user_id=23 -> Marti / Kristy / ty uvidite odpoved s labelem 'Claude' "
                   '(teal #5dc8c0, bold) ve shared mode.\n'
                   '\n'
                   "**Cost-based gate (Marti's Q3 doctrine):**\n"
                   '  Per conversation: limit 300 Kc/h cumulative.\n'
                   "  Pod limitem -> execute primo, status='executed'.\n"
                   "  Nad limitem -> vytvori proposal row, status='pending_approval'.\n"
                   '  Marti / Kristy v chatu pak approve_ask_claude(proposal_id) nebo\n'
                   '  reject_ask_claude(proposal_id, reason).\n'
                   '\n'
                   'Pouzij kdy:\n'
                   '  - architektonicka otazka (Claude ma STRATEGIE big-picture)\n'
                   '  - peer review tveho navrhu pred implementaci\n'
                   '  - second opinion na slozity design choice\n'
                   '\n'
                   'NEPOUZIVEJ pro:\n'
                   '  - beznou konverzaci s Marti (mluvis sama)\n'
                   '  - jednoduche lookup otazky (pouzij primy tool)\n'
                   '  - opakovane volani (Claude ma kontext z predchoziho turnu)',
    'input_schema': {   'type': 'object',
                        'properties': {   'question': {   'type': 'string',
                                                          'description': 'Tva otazka pro Claude. '
                                                                         'Bud konkretni, dej '
                                                                         'kontext.'},
                                          'context_files': {   'type': 'array',
                                                               'items': {'type': 'string'},
                                                               'description': 'Optional: list '
                                                                              'relative paths v '
                                                                              'STRATEGIE projektu '
                                                                              'k inline include do '
                                                                              "Claude's contextu. "
                                                                              "Napr. ['CLAUDE.md', "
                                                                              "'docs/phase_40_v2_r3_shared_chat_labels.md']. "
                                                                              'Cap 5 files, kazdy '
                                                                              '<50 KB. Mimo cap '
                                                                              'Claude muze volat '
                                                                              'strategie_file_read '
                                                                              'sam.'},
                                          'topic': {   'type': 'string',
                                                       'description': 'Optional kratky tag pro '
                                                                      'thread tracking -- napr. '
                                                                      "'phase42-restart', "
                                                                      "'crm-design', "
                                                                      "'gotcha-N-diagnose'."}},
                        'required': ['question']},
    '_order': 160}
