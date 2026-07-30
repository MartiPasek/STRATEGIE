# -*- coding: utf-8 -*-
"""Migrovaný nástroj `web_fetch` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'web_fetch',
    'description': 'Phase 27j (2.5.2026): fetch + clean markdown z libovolne URL. Doplnek k '
                   'web_search -- po vyberu relevantniho vysledku ho otevres a precteš detail. '
                   'Generic web access (NE jen pro legal): TISAX docs, vendor sites, news, '
                   'technical documentation, GDPR znění, competitive analysis, social posts, atd.\n'
                   '\n'
                   '**Vraci**: clean markdown z HTML pres markitdown (uz mas z Phase 13c RAG). '
                   'Plus title (z <title>), final URL (po redirectech), char_count (delka pred '
                   'truncate), truncated flag.\n'
                   '\n'
                   '**max_chars**: default 20 000 znaku (~5 000 tokens). Pro vetsi stranky muzes '
                   're-fetch s vyssim max_chars (hard cap 100 000). Pri truncate je v markdown '
                   "marker '[... TRUNCATED: ... znaku].'\n"
                   '\n'
                   '**Ne pouzivej pro:**\n'
                   '  - PDF -- pouzij read_pdf_structured po uploadu jako document\n'
                   '  - Image -- read_image_ocr\n'
                   "  - Binary content -- vraci error 'binary_content'\n"
                   '\n'
                   '**Workflow s web_search**:\n'
                   "  1. web_search('TISAX 2026 changes', focus='general') -> 5 results\n"
                   '  2. Vyberes [0] = oficialni TISAX news page\n'
                   "  3. web_fetch(results[0]['url']) -> markdown ~15K znaku\n"
                   '  4. Najdes v markdown sekci o nove verze v6.0\n'
                   '  5. Odpovis user + cituj URL + datum pristupu\n',
    'input_schema': {   'type': 'object',
                        'properties': {   'url': {   'type': 'string',
                                                     'description': 'Target URL (http nebo https). '
                                                                    'Z web_search vysledku nebo '
                                                                    'zadana primo userem.'},
                                          'max_chars': {   'type': 'integer',
                                                           'description': 'Max znaku co vratit. '
                                                                          'Default 20 000, hard '
                                                                          'cap 100 000. Vetsi = '
                                                                          'vetsi context cost.',
                                                           'default': 20000}},
                        'required': ['url']},
    '_order': 108}
