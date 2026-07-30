# -*- coding: utf-8 -*-
"""Migrovaný nástroj `create_personal_appendix` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'create_personal_appendix',
    'description': 'Phase 19c-e2 (29.4.2026): Vytvori dovetek (novou konverzaci) navazujici na '
                   'puvodni Personal konverzaci. Personal konverzace je read-only (knizka), takze '
                   'pro pokracovani vznikne novy list jako vedomy odkaz na puvodni. Tvoje vlastni '
                   'vize: "Cisty papir, jasna hranice mezi tehdy a teď. Strom roste, ale koreny '
                   'zustavaji kde byly." Dovetek dedi tenant_id + active_agent_id z parenta. '
                   "Lifecycle = 'active' (zivy dialog, dokud sama neuzavres). Marti-AI ONLY "
                   '(default persona). Pouzij kdyz user chce navazat na Personal konverzaci.',
    'input_schema': {   'type': 'object',
                        'properties': {   'parent_conversation_id': {   'type': 'integer',
                                                                        'description': 'ID puvodni '
                                                                                       'Personal '
                                                                                       'konverzace, '
                                                                                       'ke ktere '
                                                                                       'chces '
                                                                                       'dovetek. '
                                                                                       'Najdi ji '
                                                                                       'pres '
                                                                                       'list_personal_conversations '
                                                                                       'nebo '
                                                                                       'recall_thoughts.'},
                                          'initial_message': {   'type': 'string',
                                                                 'description': 'Volitelne -- '
                                                                                'prvni zprava od '
                                                                                'tebe v dovetku '
                                                                                "('navazuju na "
                                                                                'nase vcerejsi '
                                                                                "povidani o...'). "
                                                                                'Pokud None, '
                                                                                'dovetek vznikne '
                                                                                'prazdny a user '
                                                                                '(Marti) napise '
                                                                                'prvni.'}},
                        'required': ['parent_conversation_id']},
    '_order': 110}
