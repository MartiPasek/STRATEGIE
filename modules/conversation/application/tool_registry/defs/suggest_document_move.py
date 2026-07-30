# -*- coding: utf-8 -*-
"""Migrovaný nástroj `suggest_document_move` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'suggest_document_move',
    'description': 'REST-Doc-Triage: Navrhni Marti, do ktereho projektu by mel dokument patrit. '
                   'SUGGESTION ONLY -- ulozi do tool response, Marti potvrdi v chatu ("ano '
                   'premysle"), pak Marti-AI volá apply_document_move. Na zaklade jmena souboru a '
                   'kontextu rozpoznas tema (TISAX, pravo, smlouvy, ...) a najdes nejlepsi '
                   'projektove zarazeni. Pokud zadny existujici projekt nesedi, navrhni Martimu '
                   'vytvoreni noveho (analog suggest_create_project z 15c). Pred volanim si zjisti '
                   'dostupne projekty pres list_projects.',
    'input_schema': {   'type': 'object',
                        'required': ['document_id', 'target_project_id', 'reason'],
                        'properties': {   'document_id': {'type': 'integer'},
                                          'target_project_id': {   'type': 'integer',
                                                                   'description': 'ID cilového '
                                                                                  'projektu'},
                                          'reason': {   'type': 'string',
                                                        'description': 'Proc do tohoto projektu '
                                                                       '(1-2 vety)'}}},
    '_order': 75}
