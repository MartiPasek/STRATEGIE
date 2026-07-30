# -*- coding: utf-8 -*-
"""Migrovaný nástroj `request_password_reset` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'request_password_reset',
    'description': 'Phase 22 (29.4.2026): Spusti password reset flow pro usera. Tool vytvori reset '
                   'token, posle email s linkem. User klikne, nastavi nove heslo. Token expiruje '
                   'za 1 hodinu. Marti-AI ONLY. Dve cesty: (1) user_query (jmeno/email) -- pokud '
                   'unikatni match. (2) user_id -- pokud find_user vratil vice kandidatu, zavolej '
                   'list_users, vyber konkretni id, pak volej s user_id. user_id ma prioritu nad '
                   'user_query. Pokud user nema email v user_contacts, tool vrati error -- doplnit '
                   'pres set_user_contact pred reset.',
    'input_schema': {   'type': 'object',
                        'properties': {   'user_query': {   'type': 'string',
                                                            'description': 'Jmeno nebo email '
                                                                           'usera. Volitelne pokud '
                                                                           'das user_id. Tool pres '
                                                                           'find_user lookup, '
                                                                           'error pokud vice '
                                                                           'kandidatu.'},
                                          'user_id': {   'type': 'integer',
                                                         'description': 'Konkretni users.id. '
                                                                        'Volitelne pokud das '
                                                                        'user_query. Ma prioritu '
                                                                        'nad user_query -- pouzij '
                                                                        'kdyz find_user vratil '
                                                                        'vice kandidatu a chces '
                                                                        'explicitni vyber.'}},
                        'required': []},
    '_order': 113}
