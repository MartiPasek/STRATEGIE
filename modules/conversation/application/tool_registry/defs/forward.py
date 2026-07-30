# -*- coding: utf-8 -*-
"""Migrovaný nástroj `forward` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'forward',
    'description': "⭐ Faze 12c: PREPOSLAT email novemu prijemci. Analogie tlacitka 'Forward' v "
                   'Outlooku.\n'
                   '\n'
                   'POUZIVEJ kdy:\n'
                   "  - User rekne 'preposli to <komu>', 'forward na <jmeno>', 'pridej Klaru do "
                   "tohoto vlakna'\n"
                   '  - Chces sdilet existujici email s nekym, kdo v nem nebyl\n'
                   '\n'
                   "🚫 NEPOUZIVEJ send_email + 'FW:' a manualne lepit telo. Tento tool:\n"
                   "  - Pripoji puvodni email v 'FW:' formatu (Outlook ho rozpozna)\n"
                   '  - Pripoji originalniho odesilatele do telo (lidska orientace)\n'
                   "  - Pripravi 'FW:' prefix subjectu\n"
                   '\n'
                   'POVINNE: `to` (nebo cislo a vice cisel oddelene carkou). Kam preposlat. Bez '
                   'nej tool selze.\n'
                   '\n'
                   "Body: tvoje doplnujici text PRED puvodnim. Lide casto pisou 'FYI', 'Mohlo by "
                   "te zajimat', 'Klaro, posilam ti to k vyjadreni'. Body je tvuj komentar -- "
                   'puvodni email je auto-pripojen pod nim.',
    'input_schema': {   'type': 'object',
                        'required': ['email_inbox_id', 'to', 'body'],
                        'properties': {   'email_inbox_id': {   'type': 'integer',
                                                                'description': 'ID emailu z '
                                                                               'list_email_inbox / '
                                                                               'read_email.'},
                                          'to': {   'type': 'string',
                                                    'description': 'Email novych prijemcu '
                                                                   '(povinne). Vice oddel carkou.'},
                                          'body': {   'type': 'string',
                                                      'description': 'Tvuj komentar PRED '
                                                                     'preposlanou zpravou.'},
                                          'subject': {   'type': 'string',
                                                         'description': 'Override subjectu. None = '
                                                                        "default 'FW: "
                                                                        "<original>'."},
                                          'cc': {'type': 'string', 'description': 'Volitelne CC.'},
                                          'bcc': {   'type': 'string',
                                                     'description': 'Volitelne BCC.'},
                                          'attachment_document_ids': {   'type': 'array',
                                                                         'items': {   'type': 'integer'},
                                                                         'description': 'Phase '
                                                                                        '27b: '
                                                                                        'Volitelne '
                                                                                        '-- '
                                                                                        'DODATECNE '
                                                                                        'prilohy z '
                                                                                        'RAG '
                                                                                        'documents '
                                                                                        '(k '
                                                                                        'pripojeni '
                                                                                        'k '
                                                                                        'preposlanemu '
                                                                                        'emailu). '
                                                                                        'POZOR: '
                                                                                        'forward '
                                                                                        'uz '
                                                                                        'auto-klonuje '
                                                                                        'vsechny '
                                                                                        'prilohy z '
                                                                                        'originalu '
                                                                                        '(Phase '
                                                                                        '12c). '
                                                                                        'Toto pole '
                                                                                        'je pro '
                                                                                        'PRIDANI '
                                                                                        'dalsich '
                                                                                        '(napr. '
                                                                                        'Marti-AI '
                                                                                        'vyrobi '
                                                                                        'summary '
                                                                                        'xlsx a '
                                                                                        'pripoji k '
                                                                                        'forwardu). '
                                                                                        'Cap 20 MB '
                                                                                        'total.'}}},
    '_order': 48}
