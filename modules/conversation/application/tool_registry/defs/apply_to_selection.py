# -*- coding: utf-8 -*-
"""Migrovaný nástroj `apply_to_selection` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'apply_to_selection',
    'description': 'Provede batch akci na vsech dokumentech, ktere ma user oznacene v aktualnim '
                   'tenantu (z `list_selected_documents`). Po dokoncene akci se selection '
                   'automaticky vycisti.\n'
                   '\n'
                   "**KDY POUZIT**: VYHRADNE po explicit user's confirmu v chatu ('ano smaz "
                   "vsechny', 'jo presun je do SKOLY', 'tak je smaz'). NIKDY bez confirmu -- "
                   "destructive akce. Pokud user rekne neco neurciteho ('snad bych je smazal', "
                   "'asi je presunu'), nezavolej -- zeptej se konkretne ('Smazu vsechny vybrane? "
                   "Potvrď.').\n"
                   '\n'
                   '**ACTION TYPES**:\n'
                   "- 'delete' -- nevratne smaze dokumenty (cascade chunks/vectors/disk)\n"
                   "- 'move_to_project' -- presune do projektu, vyzaduje target_project_id\n"
                   '\n'
                   'Vraci: pocet uspesne provedenych + chyby per ID. Po teto akci selection je '
                   'prazdny -- pri dalsi konverzaci o selection volej znovu '
                   '`list_selected_documents`.',
    'input_schema': {   'type': 'object',
                        'required': ['action'],
                        'properties': {   'action': {   'type': 'string',
                                                        'enum': ['delete', 'move_to_project'],
                                                        'description': 'Typ akce. delete = '
                                                                       'nevratne, move_to_project '
                                                                       '= vyzaduje '
                                                                       'target_project_id.'},
                                          'target_project_id': {   'type': 'integer',
                                                                   'description': 'Pro '
                                                                                  "action='move_to_project': "
                                                                                  'ID cilového '
                                                                                  'projektu. Pro '
                                                                                  "'delete' "
                                                                                  'ignorovano.'}}},
    '_order': 94}
