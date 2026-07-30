# -*- coding: utf-8 -*-
"""Migrovaný nástroj `mark_todo_done` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'mark_todo_done',
    'description': "Označí TODO úkol jako hotový. Použij, když uživatel řekne 'úkol X je hotov', "
                   "'splnil jsem to', 'odškrtni X', atd. \n"
                   '\n'
                   'Dva způsoby jak zadat úkol:\n'
                   '- `thought_id` (preferované): přímé ID, když ho znáš (např. jsi zrovna   '
                   'volala list_todos).\n'
                   '- `query`: substring textu úkolu. Systém najde match v content;   když je víc '
                   'kandidátů, vrátí seznam a ty se musíš upřesnit.',
    'input_schema': {   'type': 'object',
                        'properties': {   'thought_id': {   'type': 'integer',
                                                            'description': 'Přímé ID todo myšlenky '
                                                                           '(volitelné).'},
                                          'query': {   'type': 'string',
                                                       'description': 'Substring pro vyhledání '
                                                                      'úkolu v content '
                                                                      '(volitelné).'}}},
    '_order': 22}
