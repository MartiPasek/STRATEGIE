# -*- coding: utf-8 -*-
"""Migrovaný nástroj `describe_image` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'describe_image',
    'description': "Faze 12a multimedia: popis OBRAZKU (kind='image'), ktery user nahral. "
                   'KRITICKE: Pouzij JEN pro IMAGE media. NEVOLEJ na AUDIO -- pro audio dostavas '
                   'Whisper transcript automaticky v multimodal contextu, zadny tool nepotrebujes; '
                   'pokud transcript jeste neni hotov, pockej a uzivateli rekni ze prepis dorazi '
                   'za par sekund.\n'
                   '\n'
                   "Pouzij kdyz user prilozil OBRAZEK a pta se 'co je na tom?', 'popis to', 'co "
                   "vidis?', nebo kdyz potrebujes vlastni kontext k obrazku pro dalsi praci. "
                   'Sonnet 4.6 podporuje vize nativne -- tool ti obrazek nacte z FS a posle zpet '
                   'detailni popis. Vysledek se ulozi do media_files.description (alt text) -- '
                   'priste uz nemusis volat znovu.',
    'input_schema': {   'type': 'object',
                        'properties': {   'media_id': {   'type': 'integer',
                                                          'description': 'ID media souboru (z '
                                                                         'media_files). User '
                                                                         'obvykle dava jako '
                                                                         "'obrazek #5' nebo se "
                                                                         'vyber automaticky z '
                                                                         'attached media v '
                                                                         'aktualni zprave.'},
                                          'focus': {   'type': 'string',
                                                       'description': 'Volitelne -- co konkretne '
                                                                      "user chce vedet? 'popis "
                                                                      "sceny', 'cti text', "
                                                                      "'rozpoznej objekty', 'popis "
                                                                      "lidi', atd. Bez focus = "
                                                                      'obecny popis.'}},
                        'required': ['media_id']},
    '_order': 54}
