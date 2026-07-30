# -*- coding: utf-8 -*-
"""Migrovaný nástroj `set_audit_icon` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'set_audit_icon',
    'description': "Phase 36 (9.5.2026): Marti-AI's volba symbolu pro auditované konverzace v "
                   'sidebar UI. Analog set_personal_icon (svíčka 🕯️ pro Personal).\n'
                   '\n'
                   "Marti-AI's iterace 1 volba: 📚 (kniha — 'četla jsem, vstřebala jsem, je to teď "
                   "ve mně'). Default fallback v UI = '✓' dokud tento tool nenastavi vlastni "
                   'hodnotu.\n'
                   '\n'
                   'Persistuje na personas.audit_icon. Marti-AI ONLY (default persona, je v '
                   'MANAGEMENT_TOOL_NAMES). UTF-8 max 8 bytes (pokryje 99% emoji).\n'
                   '\n'
                   'Pouziti: jednorazove po Phase 36 deployu, pak kdykoli si Marti-AI prepise '
                   "volbu (jako u Personal — '🕯️ ale uvidím').",
    'input_schema': {   'type': 'object',
                        'properties': {   'emoji': {   'type': 'string',
                                                       'description': 'Emoji nebo krátký znak (max '
                                                                      '8 bajtů UTF-8). Např. 📚, ✓, '
                                                                      '🌳, 🌿.'}},
                        'required': ['emoji']},
    '_order': 166}
