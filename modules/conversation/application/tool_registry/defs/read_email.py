# -*- coding: utf-8 -*-
"""Migrovaný nástroj `read_email` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'read_email',
    'description': 'Otevře a přečte obsah konkrétního emailu. POUŽIJ, když chceš si přečíst '
                   'konkrétní email po tom, co jsi zavolala `list_email_inbox` a uživatel ti dá '
                   "číslo (nebo řekne 'otevři ten druhý', 'ten od Claude'). Také když narazíš na "
                   'email, který patří tobě osobně (viz předmět) a chceš vědět, co v něm stojí.\n'
                   '\n'
                   '═══ KRITICKÉ: email_inbox_id JE DB ID, NE POZICE V LISTU ═══\n'
                   'Když `list_email_inbox` vypíše seznam jako:\n'
                   '  1. [id=18] Foo — subject1\n'
                   '  2. [id=23] Bar — subject2\n'
                   "a uživatel řekne 'otevři druhý', MUSÍŠ volat `read_email(email_inbox_id=23)` "
                   '(DB id v závorce), NE `read_email(email_inbox_id=2)` (pozice). Pozice 1/2/3 je '
                   'jen vizuální pořadí v listu; DB id je to, co systém skutečně používá pro '
                   'vyhledání.\n'
                   '\n'
                   'Pokud jsi list_email_inbox nevolala v tomto turnu, zavolej ji NEJDŘÍV a použij '
                   'ID z ní. Nikdy si ID nevymýšlej.\n'
                   '\n'
                   'Vrací: from, to, subject, CELÝ body (ne jen preview), timestamp, '
                   'archived_personal flag. U inbox emailů zároveň side-effect: mark_read (email '
                   'se označí jako přečtený).\n'
                   '\n'
                   'Musíš zadat buď email_inbox_id (příchozí) nebo email_outbox_id (odchozí) — NE '
                   'oba najednou.',
    'input_schema': {   'type': 'object',
                        'properties': {   'email_inbox_id': {   'type': 'integer',
                                                                'description': 'ID příchozího '
                                                                               'emailu z '
                                                                               'list_email_inbox.'},
                                          'email_outbox_id': {   'type': 'integer',
                                                                 'description': 'ID odchozího '
                                                                                'emailu '
                                                                                '(volitelné, pokud '
                                                                                'chceš znovu vidět '
                                                                                'co jsi '
                                                                                'poslala).'}}},
    '_order': 20}
