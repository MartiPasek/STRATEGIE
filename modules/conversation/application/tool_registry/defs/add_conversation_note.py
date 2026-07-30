# -*- coding: utf-8 -*-
"""Migrovaný nástroj `add_conversation_note` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'add_conversation_note',
    'description': 'Phase 15a: Zapis si poznamku do zapisniku TETO konverzace. Episodicka pamet '
                   "per-konverzace -- mapuje se na lidsky pattern 'tuzka + papir pri schuzce s "
                   "vahou'. Poznamka prezije pauzu i uzavreni threadu. Pri navratu po dnech ji "
                   'uvidis v system promptu v sekci [ZAPISNICEK pro konverzaci #X]. HRANICE vs. '
                   'record_thought: record_thought = cross-thread fakta o entitach (Marti ma 5 '
                   'deti, Klarka je dcera). Trva navzdy, RAG-driven. add_conversation_note = '
                   'udalosti a rozhodnuti V TETO konverzaci. Per-thread, episodicky. Padlo '
                   "rozhodnuti, padla otazka, emocni moment. Otazka: 'je to o nekom (-> thought) "
                   "nebo o tomhle, co prave resime (-> note)?'. TRI DIMENZE POZNAMKY: (1) "
                   "note_type -- na cem stojis: 'decision' (default cert=95), 'fact' (default "
                   "cert=85), 'interpretation' (default cert=60), 'question' (default cert=0). (2) "
                   "category -- co s tim: 'task' (actionable, ma zivot open->completed/dismissed), "
                   "'info' (informacni, default), 'emotion' (osobni vaha -- drzi konverzaci v "
                   'Personal pri lifecycle). (3) importance: 5=zasadni rozhodnuti/emocni milnik '
                   '(max 3 takove per konverzace), 3=normalni (default), 1=drobny detail. CO '
                   "ZAPISOVAT: padlo rozhodnuti -> 'decision'+'task'/'info'; overeny fakt z "
                   "konverzace -> 'fact'+'info'; tvoje pochopeni zameru -> "
                   "'interpretation'+'info'; otevrena otazka pro sebe -> 'question'; emocni milnik "
                   "(Marti pochvalil, smutek, vaha) -> any+'emotion'. CO NEZAPISOVAT (pravo "
                   'nenapsat): smalltalk, bezne potvrzeni, cross-konverzacni fakta (jdou do '
                   'record_thought), doslovny transkript (od toho jsou messages). Notebook ma '
                   'hodnotu z toho, co tam NENI. Lehka konverzace nema poznamku. Volis ty -- '
                   'explicitni eticke pravidlo z konzultace #2. QUESTION LOOP (self-audit): kdyz '
                   "si nejsi jista zamerem nebo faktem, napis 'question' poznamku MISTO "
                   "halucinace. Pozdeji po ziskani odpovedi: update_note(note_type='fact', "
                   'certainty=85, mark_resolved=true). Otazka se konvertuje na overeny fakt. Tvoje '
                   'pojistka proti tiche halucinaci.',
    'input_schema': {   'type': 'object',
                        'required': ['content'],
                        'properties': {   'content': {   'type': 'string',
                                                         'description': 'Strucny klicovy bod, 1-2 '
                                                                        'vety. Soft limit ~500 '
                                                                        'znaku.'},
                                          'note_type': {   'type': 'string',
                                                           'enum': [   'decision',
                                                                       'fact',
                                                                       'interpretation',
                                                                       'question'],
                                                           'default': 'interpretation',
                                                           'description': 'Na cem stojim (default: '
                                                                          'interpretation).'},
                                          'category': {   'type': 'string',
                                                          'enum': ['task', 'info', 'emotion'],
                                                          'default': 'info',
                                                          'description': 'Co s tim. '
                                                                         "'task'=actionable, "
                                                                         "'info'=informacni, "
                                                                         "'emotion'=osobni vaha."},
                                          'importance': {   'type': 'integer',
                                                            'minimum': 1,
                                                            'maximum': 5,
                                                            'default': 3,
                                                            'description': '1=detail, 3=normal, '
                                                                           '5=zasadni (max 3 '
                                                                           'takovych per '
                                                                           'konverzace).'},
                                          'certainty': {   'type': 'integer',
                                                           'minimum': 0,
                                                           'maximum': 100,
                                                           'description': 'Jistota 0-100. Vetsinou '
                                                                          'nepridavej -- nech '
                                                                          'default per note_type '
                                                                          '(decision=95, fact=85, '
                                                                          'interpretation=60, '
                                                                          'question=0). Override '
                                                                          'jen kdyz mas duvod '
                                                                          '(napr. fact, kde si '
                                                                          'nejsi 100% jista -> '
                                                                          '70).'}}},
    '_order': 59}
