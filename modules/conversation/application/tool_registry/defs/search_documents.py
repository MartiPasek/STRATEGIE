# -*- coding: utf-8 -*-
"""Migrovaný nástroj `search_documents` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'search_documents',
    'description': '**TENTO NASTROJ MUSIS POUZIT** kdykoli se uzivatel pta na neco, co MUZE byt v '
                   'jeho nahranych dokumentech. Pouziva semanticke vyhledavani (RAG -- pgvector + '
                   'Voyage embeddings) nad PDF, DOCX, XLSX a textovymi soubory ulozenymi v '
                   'aktualnim tenantu/projektu.\n'
                   '\n'
                   '**STROZNE PRAVIDLO:** Pokud z USER CONTEXT vis, ze uzivatel ma k dispozici '
                   "nahrane dokumenty (vidis v contextu vetu 'K dispozici ma X nahranych dokumentu "
                   "(...)'), VZDY zvazuj zda jeho dotaz NENI o necem co je v techto dokumentech. "
                   'Pokud ano = volej.\n'
                   '\n'
                   '**VOLEJ KDYZ uzivatel:**\n'
                   "- Pouzije zajmena/odkaz na dokument: 'ta smlouva', 'ten dokument', 'to PDF', "
                   "'tam byla zminka...', 'podle manualu', 'v reportu...', 'z runbooku', 'ten "
                   "dopis'\n"
                   "- Zepta se na obsah konkretniho souboru jmenovite ('Co je v X.pdf?')\n"
                   '- Ptaa se na firemni temata, ktera prirozene zijou v dokumentech: smluvy, '
                   'manualy, faktury, reporty, prezentace, normy, postupy, procedury, ceniky, '
                   'organizacni schemata, technicka dokumentace\n'
                   "- Pouzije slovni vazbu typu: 'co rikaji nase pravidla o...', 'jak to ma byt "
                   "podle...', 'co jsme se domluvili v...', 'kde je v dokumentaci...'\n"
                   '\n'
                   '**NEVOLEJ KDYZ uzivatel:**\n'
                   '- Pta se obecne znalosti (matematika, programovani, definice, jazyky)\n'
                   '- Resi spravu systemu STRATEGIE (uzivatele, projekty, persony) --   pouzij '
                   'list_users / list_projects / find_user / atd.\n'
                   '- Pise email, prepina personu nebo dela jine systemove akce\n'
                   '\n'
                   '**JAK ZPRACOVAT VYSTUP:**\n'
                   '- Vratim ti raw chunky s metadata. **Sam slozis odpoved** vlastnimi slovy, '
                   'neprepoustej ten raw blok dale uzivateli.\n'
                   '- **Vzdy citujte zdroj:** \'Podle dokumentu "Smlouva 2026.pdf" plati...\'\n'
                   "- Kdyz najdes nic relevatniho, **rekni to upimne**: 'V dostupnych dokumentech "
                   "jsem to nenasel/a, mozna to neni nahrane.'\n"
                   '\n'
                   '**SCOPE:** Tool automaticky filtruje podle aktivniho tenant + projektu. Pokud '
                   'uzivatel ma vybrany projekt, vraceji se chunky z dokumentu projektu + '
                   'tenant-globalni dokumenty. Bez projektu jen tenant-globalni.',
    'input_schema': {   'type': 'object',
                        'properties': {   'query': {   'type': 'string',
                                                       'description': 'Vyhledavaci dotaz. Stejny '
                                                                      'jazyk jako dokumenty '
                                                                      '(typicky cesky). Voyage '
                                                                      'zvlada multilingual, ale '
                                                                      'pro lepsi recall pis v '
                                                                      'jazyce dokumentu.'},
                                          'k': {   'type': 'integer',
                                                   'description': 'Pocet vraceneho top-k chunku. '
                                                                  'Default 5, max 20. Vetsi k = '
                                                                  'vetsi kontext ale vetsi token '
                                                                  'spotreba odpovedi.',
                                                   'default': 5}},
                        'required': ['query']},
    '_order': 40}
