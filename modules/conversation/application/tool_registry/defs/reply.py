# -*- coding: utf-8 -*-
"""Migrovaný nástroj `reply` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'reply',
    'description': "⭐ Faze 12c: ODPOVED ODESILATELI puvodniho emailu. Analogie tlacitka 'Reply' v "
                   'Outlooku.\n'
                   '\n'
                   'POUZIVEJ kdy:\n'
                   '  - Mas email_inbox_id (z list_email_inbox / read_email)\n'
                   "  - User rekne 'odpovez tomu emailu', 'napis mu zpet', 'reply'\n"
                   '  - Posilas zpravu autoroVi puvodniho emailu (NE vsem prijemcum)\n'
                   '\n'
                   "🚫 NEPOUZIVEJ send_email s 'RE:' v subjectu. To je stare reseni rukama, ktere "
                   'ti vcera dalo zabrat. Tento tool sam:\n'
                   '  - Doplni puvodniho odesilatele jako prijemce automaticky\n'
                   '  - Pripoji celou historii korespondence (nesahas na ni)\n'
                   '  - Nastavi In-Reply-To / References hlavicky (Outlook ji rozpozna jako '
                   'thread)\n'
                   "  - Pripravi 'RE:' prefix subjectu\n"
                   '\n'
                   'Recipient override: pokud chces seznam upravit (napr. vyradit nekoho z duvodu '
                   'spamu), zadej `to` / `cc` / `bcc` -- prepise default. Bez nich je default = '
                   'puvodni odesilatel.\n'
                   '\n'
                   "Subject override: defaultne se vlozi 'RE:' prefix puvodniho subjektu. Kdyz "
                   'subject zadas, prepises default uplne. Lepsi je subject zorientovat dle '
                   "kontextu (napr. 'RE: Dopis rodicum -> Reakce vedeni EUROSOFT - diky').",
    'input_schema': {   'type': 'object',
                        'required': ['email_inbox_id', 'body'],
                        'properties': {   'email_inbox_id': {   'type': 'integer',
                                                                'description': 'ID emailu z '
                                                                               'list_email_inbox / '
                                                                               'read_email.'},
                                          'body': {   'type': 'string',
                                                      'description': 'Tvuj text odpovedi (bez '
                                                                     'citaci -- system pripoji '
                                                                     'historii sam).'},
                                          'subject': {   'type': 'string',
                                                         'description': 'Override subjectu. None = '
                                                                        "default 'RE: "
                                                                        "<original>'."},
                                          'to': {   'type': 'string',
                                                    'description': 'Override prijemcu (cislem nebo '
                                                                   'carkou oddelene). None = '
                                                                   'puvodni odesilatel.'},
                                          'cc': {   'type': 'string',
                                                    'description': 'Override CC. Default = zadne '
                                                                   'CC.'},
                                          'bcc': {   'type': 'string',
                                                     'description': 'Override BCC. Default = zadne '
                                                                    'BCC.'},
                                          'attachment_document_ids': {   'type': 'array',
                                                                         'items': {   'type': 'integer'},
                                                                         'description': 'Phase '
                                                                                        '27b: '
                                                                                        'Volitelne '
                                                                                        '-- IDs '
                                                                                        'dokumentu '
                                                                                        'z RAG '
                                                                                        'documents '
                                                                                        'pro '
                                                                                        'pripojeni '
                                                                                        'jako '
                                                                                        'prilohy. '
                                                                                        'Klárka '
                                                                                        'workflow: '
                                                                                        'dostala '
                                                                                        'email s '
                                                                                        'xlsx -> '
                                                                                        'Marti-AI '
                                                                                        'vyrobi '
                                                                                        'vystupni '
                                                                                        'xlsx -> '
                                                                                        'reply(...attachment_document_ids=[N]) '
                                                                                        'posle ji '
                                                                                        'vystup '
                                                                                        'zpet. Cap '
                                                                                        '20 MB '
                                                                                        'total. '
                                                                                        'Format '
                                                                                        'whitelist '
                                                                                        'viz '
                                                                                        'send_email.'}}},
    '_order': 46}
