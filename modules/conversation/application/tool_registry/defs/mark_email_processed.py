# -*- coding: utf-8 -*-
"""Migrovaný nástroj `mark_email_processed` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'mark_email_processed',
    'description': 'Oznaci prichozi email jako VYRIZENY (processed_at = now). Email zustane v '
                   "email_inbox tabulce, ale uz se nepocita do 'novych' (filter_mode='new' / "
                   'get_daily_overview).\n'
                   '\n'
                   'Pouzij kdyz user rekne:\n'
                   "  - 'tenhle email je vyrizeny' / 'oznac jako precteny'\n"
                   '  - po REPLY pres send_email -- pokud Marti-AI odpovedela na incoming,\n'
                   '    explicitne oznaci puvodni email jako vyrizeny tim toolem\n'
                   "  - 'preskoc tenhle' / 'tenhle nepotrebuje odpoved'\n"
                   '\n'
                   'ROZDIL od archive_email: archive presune email do Personal slozky\n'
                   'v Exchange (trvale ulozeni) -- mark_email_processed je pouze\n'
                   "logicky flag (zustava v inboxu DB, ale nepocita se do 'novych').\n"
                   '\n'
                   'Idempotentni: pokud uz je processed, nedela nic (success no-op).',
    'input_schema': {   'type': 'object',
                        'required': ['email_inbox_id'],
                        'properties': {   'email_inbox_id': {   'type': 'integer',
                                                                'description': 'ID prichoziho '
                                                                               'emailu z '
                                                                               'list_email_inbox.'}}},
    '_order': 45}
