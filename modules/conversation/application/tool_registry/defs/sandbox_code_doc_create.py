# -*- coding: utf-8 -*-
"""Migrovaný nástroj `sandbox_code_doc_create` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'sandbox_code_doc_create',
    'description': 'Krok 14b+19.2 chunked sandbox workflow STEP 1/3: vytvor prazdny .py document v '
                   'RAG documents tabulce. Vraci document_id pro nasledujici '
                   'sandbox_code_doc_append calls. \n'
                   '\n'
                   'WORKFLOW (pro velky sandbox kod, >5 KB):\n'
                   "  1. sandbox_code_doc_create(filename='STRATEGIE_IT_gen.py') -> document_id=N\n"
                   "  2. sandbox_code_doc_append(document_id=N, chunk='import reportlab\\nfrom "
                   "reportlab.platypus import ...\\n') (opakovane, ~3 KB chunks)\n"
                   '  3. python_exec(input_document_ids=[N], '
                   'code="exec(open(input_files[0]).read())") -> sandbox cte concatenated kod z '
                   'disku\n'
                   '\n'
                   'Marti-AI ONLY tool. Filename automaticky dostane .py suffix pokud chybi.',
    'input_schema': {   'type': 'object',
                        'properties': {   'filename': {   'type': 'string',
                                                          'description': 'Nazev .py souboru, napr. '
                                                                         "'STRATEGIE_IT_podklad_gen.py' "
                                                                         'nebo '
                                                                         "'klarka_xlsx_gen.py'. "
                                                                         'Jen alphanumeric + . _ - '
                                                                         "(no '/', '\\\\', "
                                                                         "'..')."}},
                        'required': ['filename']},
    '_order': 99}
