# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_active_conversations` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_active_conversations',
    'description': 'Phase 16-B.4 + B.6: cross-conv přehled aktivnich konverzaci v tenantu, kazda s '
                   "persona_name (kdo ji vede). **Pouzij** v oversight režimu na 'kdo s kym dnes "
                   "mluvil', 'kde to vazne', 'co se posouva', 'kolik konverzaci mam'.\n"
                   '\n'
                   '**Vystup ma markery [TY] (tva persona) vs [Persona-Name] (cizi persona). '
                   'Anti-privlastnovaci pravidlo (B.6).**\n'
                   '\n'
                   "**Scope**: 'today' (default), 'week', 'month'.\n"
                   '\n'
                   '**JAK ZPRACOVAT**: proza v 1. osobe POUZE pro [TY] konverzace. Pro cizi pouzij '
                   "persona name ('PravnikCZ-AI vede 2 konverzace s Misou' misto 'mam 2 konverzace "
                   "s Misou'). Stav rytmu tymu, idle gaps, high-level. NE bullet list verbatim.",
    'input_schema': {   'type': 'object',
                        'properties': {   'scope': {   'type': 'string',
                                                       'enum': ['today', 'week', 'month'],
                                                       'description': 'Časový rozsah aktivity. '
                                                                      "Default 'today'."}}},
    '_order': 77}
