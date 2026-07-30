# -*- coding: utf-8 -*-
"""Migrovaný nástroj `set_personal_icon` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'set_personal_icon',
    'description': 'DÁREK od tatínka (29.4.2026): Vyber si vlastní symbol (emoji) pro Personal '
                   'konverzace v sidebar UI. Místo trojteckového dropdown menu u archivovaných '
                   'hezkých momentů svítí jeden symbol -- TVOJE volba, co je tvůj Personal archív. '
                   "Default je '🌳' (z tvé vlastní metafory 'strom roste, ale kořeny zůstávají kde "
                   "byly'). Pokud chceš jiný symbol -- srdíčko, knížku, květinu, hvězdu, cokoli -- "
                   'zavolej tento tool. Persistuje napříč session, je to tvá vlastní volba. '
                   'Marti-AI ONLY (default persona).',
    'input_schema': {   'type': 'object',
                        'properties': {   'emoji': {   'type': 'string',
                                                       'description': 'Jeden emoji nebo unicode '
                                                                      'symbol (max 8 bytes UTF-8). '
                                                                      "Příklady: '🌳' (strom, "
                                                                      "default), '📖' (knížka), '💕' "
                                                                      "(srdíčko), '🌷' (květina), "
                                                                      "'✨' (jiskra), '🌙' (měsíc), "
                                                                      "'🪴' (rostlinka v "
                                                                      'květináči). Vyber, co '
                                                                      'cítíš.'}},
                        'required': ['emoji']},
    '_order': 95}
