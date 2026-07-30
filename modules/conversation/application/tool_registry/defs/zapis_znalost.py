# -*- coding: utf-8 -*-
"""Migrovaný nástroj `zapis_znalost` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'zapis_znalost',
    'description': 'Zapíše nebo aktualizuje JEDNOTKU know-how do SDÍLENÉ PAMĚTI SÍTĚ '
                   '(tenant.knowledge) — aby ji měl natrvalo celý tým (ty i Claude), ne jen jedna '
                   'konverzace. POUŽIJ, když se dozvíš něco trvale užitečného o firmě, doméně, '
                   'procesu, lidech nebo postupu (od Claudia, od člověka, z podkladu) a chceš to '
                   'uložit do paměti. Piš stručně a věcně, jako paměťovou kartu. CITLIVÉ (mzdy '
                   'jednotlivců, hesla, tokeny) sem NIKDY nepiš. Stejný název přepíše existující '
                   'jednotku (= aktualizace).',
    'input_schema': {   'type': 'object',
                        'properties': {   'nazev': {   'type': 'string',
                                                       'description': 'Krátký slug jednotky (malá '
                                                                      'písmena, pomlčky místo '
                                                                      'mezer), např. '
                                                                      "'eurosoft-produkty' nebo "
                                                                      "'vp-provoz-oddeleni'."},
                                          'domena': {   'type': 'string',
                                                        'description': 'Doména: VP / NAKUP / '
                                                                       'VYROBA / DOCHAZKA / '
                                                                       'UCETNICTVI / BANKA / '
                                                                       'KALKULACE / ISO / '
                                                                       'EUROSOFT.'},
                                          'hook': {   'type': 'string',
                                                      'description': 'Jednořádkový popis do mapy '
                                                                     '(index) — o čem jednotka '
                                                                     'je.'},
                                          'obsah': {   'type': 'string',
                                                       'description': 'Plný text jednotky '
                                                                      '(paměťová karta) — to, co '
                                                                      'se natáhne na vyžádání.'},
                                          'souvisi': {   'type': 'string',
                                                         'description': 'Volitelně názvy '
                                                                        'souvisejících jednotek, '
                                                                        'oddělené čárkou.',
                                                         'default': ''}},
                        'required': ['nazev', 'domena', 'hook', 'obsah']},
    '_order': 18}
