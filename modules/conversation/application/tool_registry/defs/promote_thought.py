# -*- coding: utf-8 -*-
"""Migrovaný nástroj `promote_thought` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'promote_thought',
    'description': "Povýší existující myšlenku z 'poznámky' (note) do 'znalosti' (knowledge) — "
                   "trvalé, ověřené paměti. Použij, když user řekne něco jako 'tohle si zapiš "
                   "napevno', 'tohle už je jistý', 'promoč tu věc o X do znalostí', nebo když si "
                   'ty sama chceš ověřit/potvrdit důležitý fakt.\n'
                   '\n'
                   'MÁŠ DVĚ MOŽNOSTI JAK IDENTIFIKOVAT MYŠLENKU:\n'
                   '- `thought_id`: když znáš přímé ID (např. jsi zrovna zavolala record_thought a '
                   'víš, co se právě zapsalo). Preferovaný způsob.\n'
                   '- `query`: substring textu, podle kterého najdu myšlenku. Systém provede '
                   'substring match. Když najde 1 match, povýší ho. Když víc nebo 0, vrátí chybu a '
                   'musíš upřesnit.\n'
                   '\n'
                   'Musíš dodat ALESPOŇ jednu z nich. Když dodáš oba, `thought_id` má přednost.',
    'input_schema': {   'type': 'object',
                        'properties': {   'thought_id': {   'type': 'integer',
                                                            'description': 'ID myšlenky v DB '
                                                                           '(volitelné).'},
                                          'query': {   'type': 'string',
                                                       'description': 'Fulltext substring pro '
                                                                      'vyhledání myšlenky '
                                                                      '(volitelné). Použij '
                                                                      'stručnou klíčovou frázi, '
                                                                      "např. 'anglicky' pro "
                                                                      "myšlenku 'Kristýna mluví "
                                                                      "dobře anglicky'."}}},
    '_order': 23}
