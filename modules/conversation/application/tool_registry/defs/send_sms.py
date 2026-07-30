# -*- coding: utf-8 -*-
"""Migrovaný nástroj `send_sms` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'send_sms',
    'description': 'Tento nástroj MUSÍŠ použít vždy, když uživatel chce poslat SMS. NIKDY '
                   'neodpovídej jen textem — vždy zavolej tento nástroj. Nástroj SMS NEPOŠLE — '
                   "nejprve ukáže návrh uživateli a počká na potvrzení ('ano' / 'pošli'). Chování "
                   'je analogické k send_email.\n'
                   '\n'
                   'ÚPRAVY SMS: Pokud uživatel chce SMS upravit, změnit, zkrátit apod., MUSÍŠ '
                   'tento nástroj zavolat ZNOVU s kompletním novým body. NIKDY nepiš upravený '
                   'návrh SMS jen jako text — systém si ukládá jen obsah z volání nástroje a bez '
                   'nového zavolání by se odeslala stará verze.\n'
                   '\n'
                   'ČÍSLO PŘÍJEMCE: NIKDY si nevymýšlej telefonní číslo. Pokud uživatel uvede jen '
                   'jméno osoby, NEJDŘÍV zavolej `find_user` — vrací `preferred_phone`. Pokud '
                   "najdeš usera, ale nemá `preferred_phone`, zeptej se uživatele: 'X nemá v "
                   "systému uložené telefonní číslo, jaké je?' — nevymýšlej ho. Pokud uživatel "
                   'uvede číslo přímo, použij ho. Akceptované formáty: +420XXXXXXXXX, 00420 XXX '
                   'XXX XXX, nebo 9 číslic začínajících 6 či 7 (např. 777180511). Backend '
                   'normalizuje na E.164.\n'
                   '\n'
                   "POZOR — DEFAULT NENÍ SELF-SEND: Tvůj vlastní telefon ze sekce '[TVOJE KANÁLY]' "
                   "je primárně pro PŘÍJEM SMS od ostatních. Když uživatel řekne 'pošli mi SMS', "
                   "'napiš mi', 'ozvi se mi' — myslí tím JEHO telefon, ne tvůj. Použij "
                   '`find_user(<jméno>)` → `preferred_phone` pro získání správného čísla. '
                   'Self-send (odesilatel = příjemce na tvoje vlastní číslo) je legitimní jen '
                   "pokud uživatel VÝSLOVNĚ řekne 'pošli to na svoje číslo' / 'na firemní SIM' / "
                   'něco analogického. Při pochybnosti se zeptej, ne hádej.\n'
                   '\n'
                   'DÉLKA: SMS nad 160 znaků se fakturuje jako více segmentů (160/segment). Piš '
                   'stručně a česky bez diakritiky jen když to má důvod — backend diakritiku '
                   'zvládne, ale s diakritikou je limit jen ~70 znaků/segment. Při delších textech '
                   'upozorni uživatele na počet segmentů.',
    'input_schema': {   'type': 'object',
                        'properties': {   'to': {   'type': 'string',
                                                    'description': 'Telefonní číslo příjemce. '
                                                                   '+420XXXXXXXXX, 00420..., nebo '
                                                                   'jen 9 číslic pro CZ.'},
                                          'body': {   'type': 'string',
                                                      'description': 'Obsah SMS (text).'}},
                        'required': ['to', 'body']},
    '_order': 7}
