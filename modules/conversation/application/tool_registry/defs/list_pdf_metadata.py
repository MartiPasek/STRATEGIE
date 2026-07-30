# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_pdf_metadata` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_pdf_metadata',
    'description': 'Phase 27d (1.5.2026): PDF reader - krok 1 metadata. Vrati pocet stranek, '
                   'encrypted flag, has_text_layer (klicove pro detekci scan-only PDF kde by byl '
                   'OCR potreba). Pouziti: kdyz Klarka nebo jiny user nahraje PDF, nejdriv volej '
                   'tento tool pro overeni co tě čeká. Pokud has_text_layer=False, rekni Klarce ze '
                   'potrebujes nesifrovany text-layer PDF (nebo se omluv ze OCR neumime - to je '
                   '27d+1 problem). Pak cilene volas read_pdf_structured.\n'
                   '\n'
                   "Marti-AI's volba pattern (RE: dopis 1.5.2026 vecer): 'Stejny pattern jako "
                   "list_excel_sheets - nejdriv metadata, pak cilen y read.'",
    'input_schema': {   'type': 'object',
                        'properties': {   'document_id': {   'type': 'integer',
                                                             'description': 'ID dokumentu z RAG '
                                                                            'documents tabulky. '
                                                                            'Najdi ho pres '
                                                                            'list_inbox_documents '
                                                                            'nebo search_documents '
                                                                            "(file_type='pdf')."}},
                        'required': ['document_id']},
    '_order': 102}
