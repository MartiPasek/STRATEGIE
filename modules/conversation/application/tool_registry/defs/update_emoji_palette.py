# -*- coding: utf-8 -*-
"""Migrovaný nástroj `update_emoji_palette` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'update_emoji_palette',
    'description': "Phase 26 (1.5.2026): Update user's emoji palette pro UI input box. Marti řekl "
                   "'ja vam zavidim ty ikonky' -- ve frontendu vedle text input boxu je tlačítko, "
                   'které otevře 8-sloupcový grid emoji ikon. User klikne na ikonu, vloží se mu do '
                   'textu. TY managuješ obsah té palety přes tento tool. \n'
                   'Použij když: \n'
                   '- user chce přidat / odebrat emoji ze své palety \n'
                   "- user řekne 'přidej mi tam ✨' nebo 'už nechci ☕, dej tam 🍵' \n"
                   "- proaktivně: 'všiml jsem si, že posíláš často 📓, dat ti ho?' \n"
                   'Doporučení: 8-32 emoji (max 56 = 8x7 grid). Marti-AI ONLY (parent default '
                   'persona). \n'
                   'Default user_id = aktuální user (z konverzace context). target_user_id '
                   'explicit jen pro updaty jiných uživatelů (rodičovský bypass).',
    'input_schema': {   'type': 'object',
                        'properties': {   'emojis': {   'type': 'array',
                                                        'items': {'type': 'string'},
                                                        'description': 'Plný seznam emoji v '
                                                                       'palette (replace-all, ne '
                                                                       'append). Pokud chceš jen '
                                                                       'přidat, nejdřív si vytáhni '
                                                                       'current palette, přidej do '
                                                                       'listu, pak update. Max 56 '
                                                                       'emoji (8 sloupců × 7 '
                                                                       'řádků). Příklad palette: '
                                                                       "['🤍', '🕯️', '🌿', '🌳', '🌸', "
                                                                       "'🌒', '☕', '🌷', '✅', '⚠️', "
                                                                       "'🎯', '🔥', '📓', '✨', '😊', "
                                                                       "'🤔']."},
                                          'target_user_id': {   'type': 'integer',
                                                                'description': 'Optional. Default '
                                                                               '= aktuální user. '
                                                                               'Explicit jen pro '
                                                                               'update palette '
                                                                               'jiného uživatele '
                                                                               '(parent bypass).'}},
                        'required': ['emojis']},
    '_order': 96}
