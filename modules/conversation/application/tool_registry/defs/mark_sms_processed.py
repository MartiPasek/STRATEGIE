# -*- coding: utf-8 -*-
"""Migrovaný nástroj `mark_sms_processed` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'mark_sms_processed',
    'description': 'Oznaci prichozi SMS jako VYRIZENOU (processed_at = now). SMS zustane v '
                   "sms_inbox tabulce, ale uz se nepocita do 'novych' (get_daily_overview, "
                   'list_sms_inbox).\n'
                   '\n'
                   'Pouzij kdyz user rekne:\n'
                   "  - 'tahle SMS je vyrizena' / 'tu SMS oznac jako vyrizenou'\n"
                   '  - po REPLY pres send_sms -- pokud Marti-AI odpovedela na incoming\n'
                   "  - 'preskoc tu, neresim'\n"
                   "  - 'tady neni co odpovidat, oznac jako hotove'\n"
                   '\n'
                   'ROZDIL od dismiss_item(sms, soft/hard): dismiss_item snizi priority (SMS bude '
                   "v dalsim overview niz, ale STALE pocitana jako 'k vyrizeni'). "
                   "mark_sms_processed JI UPLNE VYRADI z 'novych' -- jako kdyby user kliknul "
                   "'oznacit jako precteny+vyrizeny' v UI.\n"
                   '\n'
                   'Idempotentni: pokud uz je processed, nedela nic (success no-op).',
    'input_schema': {   'type': 'object',
                        'required': ['sms_inbox_id'],
                        'properties': {   'sms_inbox_id': {   'type': 'integer',
                                                              'description': 'ID prichozi SMS z '
                                                                             'list_sms_inbox.'}}},
    '_order': 49}
