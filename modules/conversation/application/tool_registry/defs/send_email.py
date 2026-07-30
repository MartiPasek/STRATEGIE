# -*- coding: utf-8 -*-
"""Migrovaný nástroj `send_email` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'send_email',
    'description': 'Tento nástroj MUSÍŠ použít vždy když uživatel chce poslat email. NIKDY '
                   'neodpovídej textem o emailu — vždy zavolej tento nástroj. Nástroj email '
                   'NEPOŠLE — nejprve ukáže návrh uživateli a počká na potvrzení. \n'
                   '\n'
                   'ÚPRAVY EMAILU: Pokud uživatel chce email upravit, změnit, dodat tam něco, '
                   "smazat část, atd. (např. 'uprav', 'změň', 'dodej', 'smaž', 'doplň', 'přidej "
                   "tam'), MUSÍŠ tento nástroj zavolat ZNOVU s kompletním novým body. NIKDY nepiš "
                   'upravený návrh emailu jen jako text ve své odpovědi — systém si ukládá jen '
                   'obsah z volání nástroje a pokud nevoláš, odešle se stará verze. Toto je '
                   'kritické pravidlo.\n'
                   '\n'
                   "ADRESA PŘÍJEMCE: NIKDY si nevymýšlej email adresu ('marti@email.com', "
                   "'jan.novak@example.com' apod.). Pokud uživatel uvede jen jméno osoby a NENÍ "
                   'zřejmé jakou má email adresu, NEJPRVE zavolej `find_user` tool. Pokud '
                   'find_user nenajde nebo uživatel explicitně uvedl jinou adresu, použij tu. Když '
                   'si nejsi jistý, ZEPTEJ SE uživatele na email adresu, NIKDY ji nevymýšlej.',
    'input_schema': {   'type': 'object',
                        'properties': {   'to': {   'type': 'string',
                                                    'description': 'Email adresy příjemců (pole '
                                                                   'To:). Pro JEDNOHO příjemce '
                                                                   "zadej 'a@b.com'. Pro VÍCE "
                                                                   'příjemců zadej je ODDĚLENÉ '
                                                                   "ČÁRKAMI: 'a@b.com, c@d.com'. "
                                                                   'Backend si to rozparsuje a '
                                                                   'pošle každému samostatně — '
                                                                   'NIKDY ne jako jeden bastl.'},
                                          'cc': {   'type': 'string',
                                                    'description': 'Volitelné: CC adresa (nebo víc '
                                                                   'oddělených čárkami). Jako TO, '
                                                                   "ale příjemci jsou 'viditelní "
                                                                   "ostatním'. Použij, když user "
                                                                   "řekne 'pošli X, v kopii Y' "
                                                                   "nebo 'CC: ...'."},
                                          'bcc': {   'type': 'string',
                                                     'description': 'Volitelné: BCC adresa (skrytá '
                                                                    'kopie). Víc příjemců čárkou.'},
                                          'subject': {   'type': 'string',
                                                         'description': 'Předmět emailu'},
                                          'body': {'type': 'string', 'description': 'Tělo emailu'},
                                          'from_identity': {   'type': 'string',
                                                               'description': 'Z čí schránky email '
                                                                              'posíláš. DEFAULT je '
                                                                              "'persona' (posílá "
                                                                              'aktivní persona, '
                                                                              'typicky Marti-AI). '
                                                                              "Nastav na 'user' "
                                                                              'když uživatel '
                                                                              'výslovně řekne, že '
                                                                              'má odejít **z '
                                                                              'jeho/její** '
                                                                              'schránky — běžné '
                                                                              "spouštěče: 'pošli z "
                                                                              "mojí', 'pošli z "
                                                                              "mýho emailu', 'z "
                                                                              "mojí schránky', 'z "
                                                                              "mého účtu', 'ze "
                                                                              "mě'. Když si nejsi "
                                                                              'jistý, ZEPTEJ SE '
                                                                              'uživatele, ze které '
                                                                              'schránky to má jít. '
                                                                              'Nikdy netipuj — '
                                                                              'výchozí chování je '
                                                                              'posílat z persony.',
                                                               'enum': ['persona', 'user'],
                                                               'default': 'persona'},
                                          'attachment_document_ids': {   'type': 'array',
                                                                         'items': {   'type': 'integer'},
                                                                         'description': 'Phase 27b '
                                                                                        '(1.5.2026): '
                                                                                        'Volitelne '
                                                                                        '-- IDs '
                                                                                        'dokumentu '
                                                                                        'z RAG '
                                                                                        'documents '
                                                                                        'tabulky, '
                                                                                        'ktere '
                                                                                        'chces '
                                                                                        'pripojit '
                                                                                        'jako '
                                                                                        'prilohy. '
                                                                                        'Backend '
                                                                                        'nacte '
                                                                                        'soubor z '
                                                                                        'storage_path '
                                                                                        'a posle '
                                                                                        'pres EWS '
                                                                                        'jako '
                                                                                        'FileAttachment. '
                                                                                        'Najdi '
                                                                                        'document_id '
                                                                                        'pres '
                                                                                        'list_inbox_documents '
                                                                                        'nebo '
                                                                                        'search_documents. '
                                                                                        'Povolene '
                                                                                        'formaty: '
                                                                                        'xlsx, '
                                                                                        'xlsm, '
                                                                                        'pdf, '
                                                                                        'docx, '
                                                                                        'doc, '
                                                                                        'pptx, '
                                                                                        'csv, txt, '
                                                                                        'png, jpg, '
                                                                                        'zip, atd. '
                                                                                        '(whitelist). '
                                                                                        'Cap 20 MB '
                                                                                        'total per '
                                                                                        'email. '
                                                                                        'Workflow: '
                                                                                        'nahral '
                                                                                        'jsi '
                                                                                        'soubor / '
                                                                                        'Klárka ti '
                                                                                        'ho '
                                                                                        'poslala '
                                                                                        '-> volej '
                                                                                        'tool s '
                                                                                        '[doc_id1, '
                                                                                        'doc_id2].'},
                                          'mailbox_id': {   'type': 'integer',
                                                            'description': 'Phase 29 (4.5.2026): '
                                                                           'volitelne -- z které '
                                                                           'schránky odeslat. '
                                                                           'Default = první '
                                                                           'authorized '
                                                                           'can_send=true pro tvou '
                                                                           'personu (typicky tvá '
                                                                           'personal mailbox). '
                                                                           'Pokud chceš odeslat ze '
                                                                           'sdílené schránky '
                                                                           '(např. Pavlova '
                                                                           'pavel.zeman@), předej '
                                                                           'její id z '
                                                                           'list_mailboxes. POZOR: '
                                                                           'pro sdílené mailbox '
                                                                           'použij identity rules '
                                                                           'z [AKTIVNÍ MAILBOXY] '
                                                                           'bloku (1st turn = '
                                                                           'vlastník, RE = dual '
                                                                           'signature).'}},
                        'required': ['to', 'subject', 'body']},
    '_order': 6}
