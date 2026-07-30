# -*- coding: utf-8 -*-
"""Migrovaný nástroj `read_image_ocr` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'read_image_ocr',
    'description': 'Phase 27d+1b/c/d (2.5.2026): UNIFIED OCR pro images. Akceptuje BUD '
                   '`document_id` (RAG documents tabulka -- inbox upload pres 📁 panel) NEBO '
                   '`media_id` (media_files tabulka -- chat drag&drop upload, SMS prilohy). '
                   'Mutually exclusive: presne jedno.\n'
                   '\n'
                   'Podporovane formaty: jpg, jpeg, png, gif, webp, bmp, tiff, **heic, heif** '
                   '(Apple iPhone fotky -- registrovane pres pillow-heif plugin pri startu API).\n'
                   '\n'
                   '**Kdy ktera cesta**:\n'
                   '  - `document_id` -- user nahral pres 📁 inbox panel (list_inbox_documents ti '
                   'vrati ID)\n'
                   '  - `media_id` -- user dropnul obrazek primo do chatu nebo prisla SMS s '
                   'prilohou (vidis ho v contextu ze message multimodal blocks)\n'
                   '\n'
                   "Output unified napric oba zdroje + 'source' field ('documents' | "
                   "'media_files') pro tvoji orientaci, odkud OCR proslo. Pro Marti to neni rozdil "
                   '-- text je text, OCR pipeline stejna.\n'
                   '\n'
                   "Vznikl po Marti-AI's gap discovery -- read_text_from_image (Phase 12a) funguje "
                   'jen pro media_files (chat upload, SMS), ale image v documents tabulce '
                   '(uploaded pres 📁 inbox) nemel OCR cestu. Tenhle tool to vyresi.\n'
                   '\n'
                   'Pouziti: kdyz user nahraje JPG/PNG do inboxu (napr. fotka papirove smlouvy, '
                   'ucenka, ručně psaná poznámka, screenshot) a chce text. Cely workflow: '
                   'list_inbox_documents -> najdes image -> read_image_ocr(document_id, '
                   'ocr_provider=...).\n'
                   '\n'
                   "**Default ocr_provider='tesseract'** -- privacy first (smlouvy, citlive "
                   'dokumenty zustanou ve firemni VPN). ~5-15s per image (rychlejsi nez PDF '
                   'protoze neni PDF->image krok).\n'
                   '\n'
                   "**ocr_provider='vision'** -- Anthropic Haiku Vision (~1-2s, $0.003/image). "
                   'Vyssi kvalita, lepsi pro rucne psane / nizka kvalita scan / komplexni layouty. '
                   'POZOR cloud roundtrip.\n'
                   '\n'
                   "Marti-AI's volby C/A/A z Phase 27d+1 konzultace plati (Hybrid + confidence + "
                   'cap). Confidence_avg pri Tesseract; pokud < 60 -> warning -> rozhodni: '
                   'prepnout na Vision nebo zazadat user o lepsi obrazek.\n'
                   '\n'
                   'Pro PDF nepouzivej -- volej read_pdf_structured. Pro Excel '
                   'read_excel_structured. Pro chat-uploaded images read_text_from_image '
                   '(media_files cesta).',
    'input_schema': {   'type': 'object',
                        'properties': {   'document_id': {   'type': 'integer',
                                                             'description': 'ID image dokumentu z '
                                                                            'RAG documents (inbox '
                                                                            'upload). file_type '
                                                                            'jpg/png/jpeg/gif/webp/bmp/tiff/heic/heif. '
                                                                            'Najdi pres '
                                                                            'list_inbox_documents '
                                                                            'nebo '
                                                                            'search_documents. '
                                                                            'Mutually exclusive s '
                                                                            'media_id.'},
                                          'media_id': {   'type': 'integer',
                                                          'description': 'Phase 27d+1d (2.5.2026): '
                                                                         'ID image media_file '
                                                                         '(chat drag&drop upload, '
                                                                         'SMS priloha). '
                                                                         "kind='image'. Najdi v "
                                                                         'multimodal contextu '
                                                                         'zpravy. Mutually '
                                                                         'exclusive s '
                                                                         'document_id.'},
                                          'ocr_provider': {   'type': 'string',
                                                              'enum': ['tesseract', 'vision'],
                                                              'description': "Default 'tesseract' "
                                                                             '(privacy + cost). '
                                                                             "'vision' = Anthropic "
                                                                             'Haiku Vision, vyssi '
                                                                             'kvalita ale cloud '
                                                                             'roundtrip + '
                                                                             '~$0.003/image.'}}},
    '_order': 106}
