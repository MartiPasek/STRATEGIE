# -*- coding: utf-8 -*-
"""Migrovaný nástroj `read_text_from_image` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'read_text_from_image',
    'description': "Faze 12a multimedia: OCR -- prepis text z OBRAZKU (kind='image') do textu. JEN "
                   'pro IMAGE media, NEVOLEJ na AUDIO. Pro audio dostavas Whisper transcript '
                   'automaticky v multimodal contextu.\n'
                   '\n'
                   'Pouzij kdyz user nahral fotku dokumentu / uctenky / vizitky / screenshotu a '
                   "chce z nej vytahnout text ('precti tu uctenku', 'jaky je na te vizitce "
                   "telefon?'). Sonnet 4.6 zvlada OCR nativne, vcetne ceskeho textu. Vystup je "
                   'strukturovany text (odsazeni / odrazky zachovane podle moznosti).',
    'input_schema': {   'type': 'object',
                        'properties': {   'media_id': {   'type': 'integer',
                                                          'description': 'ID media souboru (z '
                                                                         'media_files).'},
                                          'language': {   'type': 'string',
                                                          'description': "Hint pro OCR -- 'cs' "
                                                                         "(cestina), 'en', atd. "
                                                                         "Default 'cs'."}},
                        'required': ['media_id']},
    '_order': 55}
