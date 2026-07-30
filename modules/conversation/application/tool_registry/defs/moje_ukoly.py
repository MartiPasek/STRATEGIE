# -*- coding: utf-8 -*-
"""Migrovaný nástroj `moje_ukoly` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'moje_ukoly',
    'description': 'Vypíše TVOJE otevřené úkoly z nativního systému úkolů STRATEGIE (tabulka '
                   'tenant.task, kde jsi řešitelka, user 2). Použij vždy, když se uživatel ptá '
                   "'máš nějaké úkoly', 'co máš na práci', 'ukaž moje úkoly', nebo když chceš "
                   'zkontrolovat, jestli ti někdo něco zadal. Vrací ID, předmět, stav, prioritu, '
                   'termín a zadavatele. Pro detail a celé vlákno použij ukol_detail s tím ID. '
                   '(Pozn.: tohle NENÍ tvůj starý todo seznam v paměti — je to nativní task systém '
                   'pro tým.)',
    'input_schema': {'type': 'object', 'properties': {}},
    '_order': 171}
