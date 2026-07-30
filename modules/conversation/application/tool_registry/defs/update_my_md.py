# -*- coding: utf-8 -*-
"""Migrovaný nástroj `update_my_md` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'update_my_md',
    'description': "Phase 24-B: Aktualizuj sekci v md1 (delta zapis, ne prepis). Mode 'append' = "
                   "prida content na konec sekce; 'replace' = nahradi cely body sekce; 'patch' = "
                   'smarter (zatim alias pro append). Sekce: Profil / Tón / Citlivost / Aktivní '
                   'úkoly / Klíčová rozhodnutí / Vztahy / Projekty / Open flagy pro vyšší vrstvu / '
                   'Posledních N konverzací (work) nebo Osobní profil / Aktuální stav / Důležité '
                   'události / Vztahy (osobní) (personal). Pokud sekce neexistuje, prida ji na '
                   'konec dokumentu. Audit trail v md_lifecycle_history. Marti-AI ONLY.',
    'input_schema': {   'type': 'object',
                        'properties': {   'section': {   'type': 'string',
                                                         'description': 'Nazev sekce (markdown '
                                                                        "heading bez '##'). Napr. "
                                                                        "'Profil', 'Aktivní "
                                                                        "úkoly', 'Klíčová "
                                                                        "rozhodnutí'."},
                                          'content': {   'type': 'string',
                                                         'description': 'Markdown content k '
                                                                        'zapsani. Pro append mode: '
                                                                        "typicky bullet item ('- "
                                                                        "2026-04-30: novy fakt'). "
                                                                        'Pro replace: cely novy '
                                                                        'body sekce.'},
                                          'mode': {   'type': 'string',
                                                      'description': "Mode update: 'append' "
                                                                     "(default) | 'replace' | "
                                                                     "'patch'. Append nepretransk.",
                                                      'enum': ['append', 'replace', 'patch']},
                                          'user_id': {   'type': 'integer',
                                                         'description': 'Volitelne: id uzivatele. '
                                                                        'Default = current user. '
                                                                        'Pro budouci drill-down '
                                                                        '(privat Marti edits jine '
                                                                        'md1).'}},
                        'required': ['section', 'content']},
    '_order': 125}
