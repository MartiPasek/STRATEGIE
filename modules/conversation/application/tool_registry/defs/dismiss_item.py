# -*- coding: utf-8 -*-
"""Migrovaný nástroj `dismiss_item` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'dismiss_item',
    'description': 'Faze 11c: ORCHESTRATE -- snizi priority_score polozky (email / SMS / todo) po '
                   "user rozhodnuti 'odloz' nebo 'neres'. Polozka zustava v seznamu (ne processed "
                   '/ deleted), jen klesne v prehledu. Pri pristim volani get_daily_overview uvidi '
                   'user vyriznejsi polozky nahore.\n'
                   '\n'
                   'VOLEJ kdyz user v orchestrate cyklu rekne:\n'
                   "  - 'odloz' / 'pozdeji' / 'jindy'  -> level='soft' (-10 priority)\n"
                   "  - 'neres' / 'dnes ne' / 'nech'   -> level='hard' (-30 priority)\n"
                   '\n'
                   "NEVOLEJ kdyz user rekne 'preskoc' -- to znamena 'dneska vynech bez "
                   "persistence', polozka si drzi puvodni prioritu, jen skok na dalsi.\n"
                   '\n'
                   "Po uspesnem volani potvrdi slovy ('OK, odkladam' / 'OK preskocime dnes')\n"
                   'a pokracuj na dalsi polozku v cyklu.',
    'input_schema': {   'type': 'object',
                        'properties': {   'source_type': {   'type': 'string',
                                                             'enum': ['email', 'sms', 'todo'],
                                                             'description': 'Typ polozky -- '
                                                                            'email_inbox.id / '
                                                                            'sms_inbox.id / '
                                                                            'thoughts.id.'},
                                          'source_id': {   'type': 'integer',
                                                           'description': 'ID polozky (z '
                                                                          'get_daily_overview '
                                                                          "response, field 'id')."},
                                          'level': {   'type': 'string',
                                                       'enum': ['soft', 'hard'],
                                                       'description': "'soft' = odloz (-10 "
                                                                      "priority), 'hard' = neres "
                                                                      '(-30 priority).'}},
                        'required': ['source_type', 'source_id', 'level']},
    '_order': 51}
