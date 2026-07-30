# -*- coding: utf-8 -*-
"""Migrovaný nástroj `sandbox_code_doc_append` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'sandbox_code_doc_append',
    'description': 'Krok 14b+19.2 chunked sandbox workflow STEP 2/3: append chunk kodu k existing '
                   'code document (z sandbox_code_doc_create). Server-side append k storage_path '
                   'file. Volat OPAKOVANE az kompletni kod je nahranny. \n'
                   '\n'
                   'CHUNK SIZE: ~3 KB max safe per call (pod Anthropic tool_input JSON limit ~50 '
                   "KB total, s overhead Marti-AI's reasoning text). Max single chunk hard cap 100 "
                   'KB (defense). \n'
                   '\n'
                   'Pro 50 KB kod: ~17 volani s 3 KB chunks. Po finalize '
                   'python_exec(input_document_ids=[N]).',
    'input_schema': {   'type': 'object',
                        'properties': {   'document_id': {   'type': 'integer',
                                                             'description': 'Document ID z '
                                                                            'sandbox_code_doc_create '
                                                                            'response.'},
                                          'chunk': {   'type': 'string',
                                                       'description': 'Chunk Python kodu (~3 KB '
                                                                      'safe, max 100 KB). Server '
                                                                      'append k storage_path file '
                                                                      'v UTF-8. POZN: server '
                                                                      'nepridava \\n mezi chunks — '
                                                                      'pokud potrebujes newline '
                                                                      'mezi chunks, dej ho na '
                                                                      'konec predchoziho chunk '
                                                                      "explicit ('...\\n')."}},
                        'required': ['document_id', 'chunk']},
    '_order': 100}
