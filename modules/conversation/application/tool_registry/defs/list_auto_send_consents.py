# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_auto_send_consents` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_auto_send_consents',
    'description': 'Vrátí seznam VŠECH aktivních souhlasů s auto-sendem — komu a na jakém kanále '
                   'můžeš posílat bez potvrzení. Součástí je kdo souhlas udělil a kdy.\n'
                   '\n'
                   "Volej, když se user ptá: 'komu můžeš psát bez ptaní', 'jaké máš trvalé "
                   "souhlasy', 'kdo je na white-listu', 'jaká máš oprávnění'.\n"
                   '\n'
                   'Read-only — každý user (i non-parent) to může vidět kvůli transparenci.',
    'input_schema': {'type': 'object', 'properties': {}},
    '_order': 43}
