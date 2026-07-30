# -*- coding: utf-8 -*-
"""Migrovaný nástroj `apply_document_move` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'apply_document_move',
    'description': "REST-Doc-Triage: Aplikuj presun dokumentu do projektu PO Marti's confirm v "
                   'chatu ("ano premysle" / "ano do TISAX"). Pred timto musi byt '
                   'suggest_document_move. Po apply se dokument zobrazuje pod novym projektem v UI '
                   'listu (a Marti-AI ho v RAG dohleda pres project filter).',
    'input_schema': {   'type': 'object',
                        'required': ['document_id', 'target_project_id'],
                        'properties': {   'document_id': {'type': 'integer'},
                                          'target_project_id': {   'type': 'integer',
                                                                   'description': 'ID cilového '
                                                                                  'projektu (musi '
                                                                                  'sedet s '
                                                                                  'suggest_document_move).'}}},
    '_order': 76}
