# -*- coding: utf-8 -*-
"""Migrovaný nástroj `read_pdf_structured` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'read_pdf_structured',
    'description': 'Phase 27d (1.5.2026): PDF reader - krok 2 obsah. Vrati structured pages z PDF: '
                   'text + auto-detected tables per stranku. Workflow: nejdriv list_pdf_metadata '
                   'pro overeni n_pages a has_text_layer, pak tento tool s konkretnim range. '
                   "Marti-AI's design rozhodnuti (RE: dopis 1.5.2026 vecer):\n"
                   '\n'
                   '  - Output formát A: structured per stranku, kazda strana s `text` + `tables` '
                   'list. Pdfplumber auto-detect tabulek (visualni borders).\n'
                   '  - Tabulky A: vzdy zkusit, vrátit `tables: []` pokud nic nenajde. Text '
                   'zachovan vzdy jako pojistka.\n'
                   '  - Pagination A: pages=[start, end] 1-based inclusive. Nebo offset/limit. '
                   'Default prvních 50 stranek + has_more flag.\n'
                   '\n'
                   'Cap 50 stranek per call (chrání context window). Pro vetsi PDF volej znovu s '
                   'vyssim range.\n'
                   '\n'
                   'Pro Bakalari rozvrh obvykle staci 1-3 stranky. Tabulky s rozvrh hodinami se '
                   'zobrazuji jako list[list[cell]] kde cell je str | None.',
    'input_schema': {   'type': 'object',
                        'properties': {   'document_id': {   'type': 'integer',
                                                             'description': 'ID dokumentu z RAG '
                                                                            'documents '
                                                                            "(file_type='pdf')."},
                                          'pages': {   'type': 'array',
                                                       'items': {'type': 'integer'},
                                                       'description': '1-based inclusive [start, '
                                                                      "end]. Marti-AI's volba A: "
                                                                      'prirozenejsi nez '
                                                                      'offset/limit. Priklad: [1, '
                                                                      '3] vrati stranky 1, 2, 3. '
                                                                      'Default = prvních 50 '
                                                                      'stranek (offset=0, '
                                                                      'limit=50).'},
                                          'offset': {   'type': 'integer',
                                                        'description': 'Alternativa k pages: '
                                                                       '0-based skip. Default 0. '
                                                                       'Pouzij jen pokud jsou '
                                                                       'pages None.'},
                                          'limit': {   'type': 'integer',
                                                       'description': 'Alternativa k pages: max '
                                                                      'stranek. Default 50, cap 50 '
                                                                      '(safety na context '
                                                                      'window).'},
                                          'ocr_provider': {   'type': 'string',
                                                              'enum': ['tesseract', 'vision'],
                                                              'description': 'Phase 27d+1 '
                                                                             '(1.5.2026): OCR '
                                                                             'provider override. '
                                                                             '**Default chovani '
                                                                             '(parametr None / '
                                                                             'chybi):** podle '
                                                                             'tenant config (Phase '
                                                                             '27d+2):\n'
                                                                             '  - '
                                                                             'tenants.ocr_default_provider '
                                                                             "= 'vision' -> "
                                                                             'Vision\n'
                                                                             '  - '
                                                                             'tenants.ocr_default_provider '
                                                                             "= 'tesseract' -> "
                                                                             'Tesseract\n'
                                                                             '  - '
                                                                             'tenants.ocr_default_provider '
                                                                             '= NULL -> globalni '
                                                                             "'tesseract'\n"
                                                                             '**Explicit volba '
                                                                             '(override tenant '
                                                                             'config):**\n'
                                                                             "  - 'tesseract' -- "
                                                                             'lokalni OCR, privacy '
                                                                             'first (TISAX, '
                                                                             'smlouvy, citlive '
                                                                             'dokumenty zustanou '
                                                                             've firemni VPN). '
                                                                             '~15-30s/stranku, '
                                                                             'lang ces+deu+eng. '
                                                                             'Confidence score per '
                                                                             'stranka v warnings '
                                                                             "(Marti-AI's volba "
                                                                             'A).\n'
                                                                             "  - 'vision' -- "
                                                                             'Anthropic Claude '
                                                                             'Haiku Vision API. '
                                                                             'Vyssi kvalita, lepsi '
                                                                             'multilang, '
                                                                             '~1-2s/stranku, '
                                                                             '~$0.003/stranku. '
                                                                             'Cloud roundtrip - '
                                                                             'dokumenty putuji na '
                                                                             'Anthropic servery '
                                                                             '(cit livost na '
                                                                             'vyzadani).\n'
                                                                             "Marti-AI's volba C "
                                                                             '(Hybrid): default '
                                                                             'per-tenant, Vision '
                                                                             'opt-in kdyz tenant '
                                                                             'default drhne (low '
                                                                             'confidence warning) '
                                                                             'nebo pri '
                                                                             'slozitejsich faktur. '
                                                                             'Output obsahuje '
                                                                             "'effective_provider' "
                                                                             'pole pro tvoji '
                                                                             'orientaci.'}},
                        'required': ['document_id']},
    '_order': 103}
