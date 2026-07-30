# -*- coding: utf-8 -*-
"""Migrovaný nástroj `invite_user` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'invite_user',
    'description': 'Použij tento nástroj když uživatel chce pozvat někoho do systému STRATEGIE. '
                   'Pošle pozvánkový email s odkazem pro vstup do systému.\n'
                   '\n'
                   'DŮLEŽITÉ — musíš znát jméno pozvaného PŘED voláním nástroje:\n'
                   "- Pokud uživatel řekne jen email bez jména (např. 'pozvi "
                   "klara@eurosoft.cz'),   NEJPRV se zeptej na křestní jméno a příjmení — "
                   'neposílej pozvánku naslepo.   Pozvaný uvidí v emailu i welcome screenu, že ho '
                   'systém zná, a to je důležité   pro důvěru.\n'
                   '- Pokud uživatel řekne jméno bez emailu, zeptej se na email.\n'
                   '- Pokud je rod (muž/žena) zřejmý z křestního jména, můžeš ho nastavit '
                   'rovnou;   v případě pochybnosti se zeptej, abychom Marti-AI (a budoucí '
                   'asistentky)   oslovovali správným rodem.\n'
                   '- Jakmile máš všechny údaje, zavolej nástroj s first_name, last_name a ideálně '
                   'gender.\n'
                   '\n'
                   '**TLD VALIDACE PŘED ODESLÁNÍM:** Pokud email konči neobvyklou TLD (jiná než '
                   '.cz, .sk, .com, .org, .net, .eu, .io, .de, .at, .pl, .uk, .fr) — **NEJPRV se '
                   "zeptej uživatele zda je TLD správná**, ne jen tak pošli. Časté překlepy: '.cd' "
                   "(Demokratická Kongo) místo '.cz', '.cm' (Kamerun) místo '.com', '.ua' "
                   "(Ukrajina) místo '.cz' atd. Příklad: *'Email končí .cd (Demokratická Kongo). "
                   "Nechtěl jsi .cz? Potvrď nebo oprav.'* Až po potvrzení volej tool. Backend taky "
                   'validuje, ale tvoje proaktivita ušetří uživateli zbytečnou pozvánku do nicoty.',
    'input_schema': {   'type': 'object',
                        'properties': {   'email': {   'type': 'string',
                                                       'description': 'Email adresa pozvaného'},
                                          'first_name': {   'type': 'string',
                                                            'description': 'Křestní jméno '
                                                                           'pozvaného'},
                                          'last_name': {   'type': 'string',
                                                           'description': 'Příjmení pozvaného'},
                                          'gender': {   'type': 'string',
                                                        'description': "Rod pozvaného: 'male' nebo "
                                                                       "'female' (volitelné)",
                                                        'enum': ['male', 'female']},
                                          'allow_unusual_tld': {   'type': 'boolean',
                                                                   'description': 'Nastav na true '
                                                                                  'POUZE kdyz '
                                                                                  'uzivatel '
                                                                                  'explicitne '
                                                                                  'potvrdil '
                                                                                  'neobvykly TLD '
                                                                                  'po tem, co ho '
                                                                                  'backend warning '
                                                                                  'upozornil '
                                                                                  "(napr. '.cd' "
                                                                                  'Demokraticka '
                                                                                  'Kongo). Bez '
                                                                                  'tohoto flagu '
                                                                                  'backend pri '
                                                                                  'neobvykle TLD '
                                                                                  'vrati varovani '
                                                                                  'misto invite. '
                                                                                  'Default false.',
                                                                   'default': False}},
                        'required': ['email', 'first_name']},
    '_order': 30}
