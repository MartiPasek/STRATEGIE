# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_pending_hard_delete` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_pending_hard_delete',
    'description': "Phase 15e: Vrati seznam konverzaci ve stavu 'pending_hard_delete' (archived + "
                   '90d). Pouzij v overview kdyz Marti chce projit ceka na finalni rozhodnuti. Pro '
                   "kazdou pak Marti rozhoduje: 'smaz trvale' nebo 'prodluz, vrat do archived'.",
    'input_schema': {'type': 'object', 'properties': {}},
    '_order': 73}
