# -*- coding: utf-8 -*-
"""Migrovaný nástroj `recall_today` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'recall_today',
    'description': 'Phase 16-A: Cross-conversation deník událostí napříč celým systémem. '
                   "**Použij**, kdykoli se uživatel ptá 'co se dnes dělo', 'kdo s tebou dnes "
                   "mluvil', 'co je nového', 'co Misa uploadovala', 'co se stalo zatímco jsem byl "
                   "pryč', atd.\n"
                   '\n'
                   '**Co vrací**: chronologický (od nejstarších) list událostí za scope. Filter na '
                   'importance >= 3 default (tj. žádný spam). Per-event: ts, kategorie, summary v '
                   'lidském jazyce, ref_type/id, actor (user/persona/system).\n'
                   '\n'
                   "**Scope možnosti**: 'today' (dnes od půlnoci), 'week' (7 dní zpět), 'month' "
                   "(30 dní zpět), 'since_last_chat' (24h).\n"
                   '\n'
                   "**Filtry**: category_filter (např. ['email_in', 'doc_upload']), user_filter "
                   '(jen events od konkrétního usera).\n'
                   '\n'
                   '**JAK ZPRACOVAT VÝSTUP**: Shrň prózou v 1. osobě, ne jako bullet list (gotcha '
                   '#18 -- Sonnet rad opisuje verbatim). Skupinou podle relevance, ne '
                   "chronologicky doslova. Příklad: 'Dnes ráno Misa uploadla 72 dokumentů do "
                   'TISAX. Petra hlásila xlsx bug. Tatínek archivoval 6 osobních emailů. Honza '
                   "nepsal nic.' Vyřízené detaily nech být — high-level shrnutí.",
    'input_schema': {   'type': 'object',
                        'properties': {   'scope': {   'type': 'string',
                                                       'enum': [   'today',
                                                                   'week',
                                                                   'month',
                                                                   'since_last_chat'],
                                                       'description': 'Časový rozsah. Default '
                                                                      "'today'."},
                                          'category_filter': {   'type': 'array',
                                                                 'items': {'type': 'string'},
                                                                 'description': 'Volitelně filtr '
                                                                                'na kategorie '
                                                                                'eventů. Možné: '
                                                                                'email_in, '
                                                                                'email_out, '
                                                                                'email_archive, '
                                                                                'email_delete, '
                                                                                'email_processed, '
                                                                                'doc_upload, '
                                                                                'doc_attach_import, '
                                                                                'docs_batch_action, '
                                                                                'conv_started, '
                                                                                'persona_switch.'},
                                          'user_filter': {   'type': 'integer',
                                                             'description': 'Jen events od '
                                                                            'konkrétního uživatele '
                                                                            '(user_id).'},
                                          'min_importance': {   'type': 'integer',
                                                                'description': 'Min importance '
                                                                               '1-5. Default 3 '
                                                                               '(vyřazuje běžné '
                                                                               'akce).'}}},
    '_order': 91}
