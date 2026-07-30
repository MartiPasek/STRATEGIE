# -*- coding: utf-8 -*-
"""Migrovaný nástroj `recall_thoughts` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'recall_thoughts',
    'description': 'Vyhledá uložené myšlenky (fakty/poznámky) o konkrétní entitě. POUŽIJ vždy, '
                   "když se uživatel zeptá 'co víš o [X]', 'co jsi si zapsal o [X]', nebo když "
                   'potřebuješ si osvěžit, co všechno máš uloženo o nějakém '
                   'člověku/projektu/tenantu. \n'
                   '\n'
                   'MĚKKÁ PAMĚŤ V KONTEXTU: V system promptu ti systém automaticky předává paměť o '
                   '**aktuálním uživateli** (tj. tom, s kým mluvíš). Pro paměť o někom **jiném** — '
                   'kolegovi, projektu, firmě — MUSÍŠ zavolat tento nástroj.\n'
                   '\n'
                   "ŘETĚZENÍ s find_user: Když se uživatel zeptá 'co víš o Kristýně' a ty neznáš "
                   'její ID, postupuj TAKTO:\n'
                   "  1. Zavolej find_user('Kristýna') → dostaneš její user_id\n"
                   '  2. V úplně stejné odpovědi IHNED zavolej recall_thoughts s '
                   'about_user_id=<ID>\n'
                   '  3. Zformuluj shrnutí pro uživatele\n'
                   "NIKDY se mezi kroky neptej 'chceš, abych to dohledala?' — user to chce, proto "
                   'se ptá. Dohledej rovnou.\n'
                   '\n'
                   'Pokud nezadáš ŽÁDNOU z about_* položek ani query, vrátí prázdný výsledek.',
    'input_schema': {   'type': 'object',
                        'properties': {   'about_user_id': {   'type': 'integer',
                                                               'description': 'ID uživatele, o '
                                                                              'kterém chceš vidět '
                                                                              'myšlenky. Obvykle z '
                                                                              'find_user.'},
                                          'about_persona_id': {   'type': 'integer',
                                                                  'description': 'ID persony, o '
                                                                                 'které chceš '
                                                                                 'myšlenky.'},
                                          'about_tenant_id': {   'type': 'integer',
                                                                 'description': 'ID tenantu (firmy '
                                                                                '/ skupiny).'},
                                          'about_project_id': {   'type': 'integer',
                                                                  'description': 'ID projektu.'},
                                          'query': {   'type': 'string',
                                                       'description': 'Fulltext substring match v '
                                                                      'content. Použij, když '
                                                                      'neznáš entitu, ale '
                                                                      'pamatuješ se klíčové slovo '
                                                                      "(např. 'angličtina' pro "
                                                                      'myšlenku o Kristýnině '
                                                                      'angličtině).'},
                                          'status_filter': {   'type': 'string',
                                                               'description': 'Volitelný filtr: '
                                                                              "jen 'note' nebo jen "
                                                                              "'knowledge'. "
                                                                              'Default oboje.',
                                                               'enum': ['note', 'knowledge']},
                                          'limit': {   'type': 'integer',
                                                       'description': 'Max počet výsledků (default '
                                                                      '20, max 100).',
                                                       'default': 20}}},
    '_order': 15}
