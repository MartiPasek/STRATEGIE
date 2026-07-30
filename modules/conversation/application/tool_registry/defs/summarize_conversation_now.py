# -*- coding: utf-8 -*-
"""Migrovaný nástroj `summarize_conversation_now` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'summarize_conversation_now',
    'description': 'Vytvoří shrnutí aktuální konverzace — vynutí summary job HNED, nečeká na '
                   'threshold. Po úspěchu se stará historie konverzace nahradí krátkým shrnutím a '
                   'API calls jsou výrazně lehčí.\n'
                   '\n'
                   "POUŽIJ, když uživatel odpoví 'ano / zkrať / shrň' na tvou otázku nebo sám "
                   "řekne 'shrň konverzaci, zkrať to'. Sama se **neptej** ihned při každé zprávě — "
                   'nabídni shrnutí jen kdyz je konverzace skutečně dlouhá (system metadata ti '
                   'řeknou).',
    'input_schema': {'type': 'object', 'properties': {}},
    '_order': 19}
