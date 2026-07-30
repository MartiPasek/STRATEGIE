# -*- coding: utf-8 -*-
"""Migrovaný nástroj `web_search` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'web_search',
    'description': "Phase 27j (2.5.2026): vyhledavani na webu pres Brave Search API. Marti-AI's "
                   'request po Sarka HR case (zastaralu legislativu opravila uzivatelka). Pouzij '
                   'VZDY kdyz aktualnost informace ma vahu -- legislativa, certifikace, ceny, '
                   'novinky, tech docs, vendor sites.\n'
                   '\n'
                   '**Workflow**: web_search vrati 5-10 vysledku (title + snippet + URL) -> ty si '
                   'vyberes nejrelevantnejsi -> web_fetch(url) na detail -> vytahnes z markdown '
                   'obsahu konkretni info -> citujes URL + datum.\n'
                   '\n'
                   '**focus values**:\n'
                   "  - `'general'` (default) -- bezne vyhledavani, vsechny zdroje\n"
                   "  - `'legal'` -- prefer Czech/EU pravni databaze (zakonyprolidi.cz,     "
                   'justice.cz, mvcr.cz, gov.cz, eur-lex.europa.eu). Site filter     rankuje vys, '
                   'ale i jine zdroje mohou byt vraceny.\n'
                   "  - `'news'` -- past week filter pro aktualnost.\n"
                   '\n'
                   '**Citation pattern (povinna pri vsech legal/HR/compliance odpovedich)**: uvest '
                   "URL + datum pristupu. Priklad: 'Podle § 35 ZP (citováno z zakonyprolidi.cz, "
                   "2.5.2026)...'\n"
                   '\n'
                   'Output ma is_legal_source flag per result -- ukazuje jestli URL spada do legal '
                   'whitelist. published_date pokud je k dispozici.',
    'input_schema': {   'type': 'object',
                        'properties': {   'query': {   'type': 'string',
                                                       'description': 'Search query (Czech / '
                                                                      'English / multilang). Buď '
                                                                      "konkrétní -- 'zkušební doba "
                                                                      "zákoník práce 2026' lépe "
                                                                      "než 'práce'."},
                                          'n_results': {   'type': 'integer',
                                                           'description': 'Pocet vysledku k '
                                                                          'vraceni. Default 5, max '
                                                                          '10. Vetsi = vetsi '
                                                                          'context, drazsi token '
                                                                          'cost.',
                                                           'default': 5},
                                          'focus': {   'type': 'string',
                                                       'enum': ['general', 'legal', 'news'],
                                                       'description': 'general (vse), legal (CZ/EU '
                                                                      'pravni databaze priority), '
                                                                      'news (past week).',
                                                       'default': 'general'}},
                        'required': ['query']},
    '_order': 107}
