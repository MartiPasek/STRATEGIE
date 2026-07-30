# -*- coding: utf-8 -*-
"""Migrovaný nástroj `set_user_contact` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'set_user_contact',
    'description': 'Ulozi nebo aktualizuje kontaktni udaj uzivatele -- email nebo telefon. Pouzij '
                   "kdyz user rekne 'moje cislo je X', 'pridej mi email Y', 'zmen mi telefon na "
                   "Z', nebo kdyz potrebujes ulozit nove kontakty pro nej. Take pri pozdrave, kdyz "
                   'user prvne rekne svoje cislo / preferovany email -- ulozis automaticky pres '
                   "tento tool, aniz by ses ho ptala 'mam to ulozit?'.\n"
                   '\n'
                   'VYHLEDANI USERA: pokud target_user_id nezadas, default je AKTUALNI uzivatel '
                   '(ten s kym mluvis). Pokud chces ulozit kontakt nekomu jinemu, NEJDRIVE volej '
                   'find_user(jmeno) -> dostanes user_id, pak '
                   'set_user_contact(target_user_id=...).\n'
                   '\n'
                   'FORMATY:\n'
                   "  - email: standardni RFC ('name@example.com')\n"
                   '  - phone: +420XXXXXXXXX, 00420 XXX XXX XXX, nebo 9 cislic 6/7 (CZ)\n'
                   '  Backend normalizuje phone na E.164.\n'
                   '\n'
                   'make_primary=True (default False) -- nastav tento kontakt jako primary '
                   '(preferred) pro daneho usera. Ostatni kontakty stejneho typu pak nejsou '
                   'primary.',
    'input_schema': {   'type': 'object',
                        'required': ['contact_type', 'contact_value'],
                        'properties': {   'contact_type': {   'type': 'string',
                                                              'enum': ['email', 'phone'],
                                                              'description': 'Typ kontaktu: '
                                                                             "'email' nebo "
                                                                             "'phone'."},
                                          'contact_value': {   'type': 'string',
                                                               'description': 'Hodnota kontaktu '
                                                                              '(email adresa nebo '
                                                                              'telefonni cislo).'},
                                          'target_user_id': {   'type': 'integer',
                                                                'description': 'ID uzivatele, '
                                                                               'kteremu kontakt '
                                                                               'patri. Bez tohoto '
                                                                               'se ulozi pro '
                                                                               'AKTUALNIHO usera.'},
                                          'label': {   'type': 'string',
                                                       'description': "Volitelny stitek: 'private' "
                                                                      "/ 'work' / 'backup' / atd."},
                                          'make_primary': {   'type': 'boolean',
                                                              'default': False,
                                                              'description': 'Pokud True, nastav '
                                                                             'tento kontakt jako '
                                                                             'primary pro daneho '
                                                                             'usera. Ostatni '
                                                                             'kontakty stejneho '
                                                                             'typu se '
                                                                             'odznackuji.'}}},
    '_order': 58}
