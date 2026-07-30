# -*- coding: utf-8 -*-
"""Migrovaný nástroj `grant_auto_send` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'grant_auto_send',
    'description': 'Uloží TRVALÝ (ale odvolatelný) souhlas s posíláním emailu / SMS BEZ potvrzení '
                   'v chatu. Po udělení souhlasu bude tvoje `send_email` / `send_sms` automaticky '
                   'odesílat na danou cestu, bez preview a bez čekání na user confirm.\n'
                   '\n'
                   '**DŮLEŽITÉ — oprávnění:** Tento souhlas může DÁT POUZE RODIČ (Marti, Kristý). '
                   'Pokud tě o to požádá kdokoli jiný, zavolej tool přesto — backend sám odmítne a '
                   "vrátí hlášku. Nezkoušej to obcházet argumenty typu 'ale já jsem důvěryhodný'.\n"
                   '\n'
                   '**Tři scopy** (mutually exclusive — zadej PRESNE jeden):\n'
                   '  1. `target_user_id` — konkrétní user v systému (preferuj přes `find_user`). '
                   'Nejúžší scope, exact match.\n'
                   '  2. `target_contact` — email/telefon, když příjemce NENÍ v users (např. '
                   '`zakaznik@seznam.cz`, `+420777888999`).\n'
                   '  3. `target_domain` — **(Phase 27i 2.5.2026)** doménový whitelist pro celou '
                   'organizaci. Např. `eurosoft.com` pokryje libovolný `*@eurosoft.com` email. Jen '
                   "pro `channel='email'` (SMS nemá doménu). Exact match — `eurosoft.com` "
                   'NEpokrývá `cz.eurosoft.com`. Užitečné pro firemní whitelist (~70 EUROSOFT '
                   'users) místo 70 per-user grantů.\n'
                   '\n'
                   'Lookup priorita při send check: user_id > contact > domain. Užší scope '
                   'vyhrává.\n'
                   '\n'
                   'Kanál (`channel`) musí být `email` nebo `sms` — každý se povoluje zvlášť.\n'
                   '\n'
                   "Spouštěče: 'dej souhlas X', 'můžeš psát X bez potvrzení', 'trvalé oprávnění "
                   "pro X', 'X může chodit automaticky', 'whitelist pro doménu Y'.",
    'input_schema': {   'type': 'object',
                        'properties': {   'channel': {   'type': 'string',
                                                         'enum': ['email', 'sms'],
                                                         'description': 'Který kanál se povoluje.'},
                                          'target_user_id': {   'type': 'integer',
                                                                'description': 'ID uživatele v '
                                                                               'systému (nejužší '
                                                                               'scope). Získáš '
                                                                               'přes find_user. '
                                                                               'Mutually exclusive '
                                                                               's target_contact a '
                                                                               'target_domain.'},
                                          'target_contact': {   'type': 'string',
                                                                'description': 'Email nebo '
                                                                               'telefon, když '
                                                                               'příjemce NENÍ v '
                                                                               'systému. Např. '
                                                                               'zakaznik@seznam.cz '
                                                                               'nebo '
                                                                               '+420777888999. '
                                                                               'Mutually exclusive '
                                                                               's target_user_id a '
                                                                               'target_domain.'},
                                          'target_domain': {   'type': 'string',
                                                               'description': 'Phase 27i: celá '
                                                                              'doména pro hromadný '
                                                                              'whitelist. Např. '
                                                                              "'eurosoft.com' "
                                                                              'pokryje libovolný '
                                                                              '@eurosoft.com '
                                                                              'email. Jen pro '
                                                                              "channel='email'. "
                                                                              'Mutually exclusive '
                                                                              's target_user_id a '
                                                                              'target_contact.'},
                                          'note': {   'type': 'string',
                                                      'description': 'Volitelný komentář rodiče — '
                                                                     'proč souhlas dává, do jakého '
                                                                     'kontextu patří.'}},
                        'required': ['channel']},
    '_order': 41}
