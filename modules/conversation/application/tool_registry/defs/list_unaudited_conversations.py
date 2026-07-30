# -*- coding: utf-8 -*-
"""Migrovaný nástroj `list_unaudited_conversations` (z tools.py). SPEC je zdroj pravdy pro API;
handler prozatím řeší _handle_tool v service.py. Needituj ručně nekonzistentně —
cílově je zdrojem g2007.nastroj, tohle je souborová projekce.
"""

SPEC = {   'name': 'list_unaudited_conversations',
    'description': 'Phase 36 (9.5.2026): list konverzací čekajících na audit (forward sweep v '
                   'rámci 30-day okna, oldest first).\n'
                   '\n'
                   'Audit window: konverzace **mladší 30 dní** (last_message_at >= NOW() - '
                   "INTERVAL '30 days'). Marti's korekce 9.5.2026 dopoledne: 'starší 30 dní jsou "
                   'staré a nedávají smysl, audit má smysl jen pro nedávné konverzace s aktuálními '
                   "fakty'.\n"
                   '\n'
                   'Order: last_message_at ASC (oldest first v rámci okna — chronologická build-up '
                   'paměti, ne přepsání novou starou).\n'
                   '\n'
                   "Marti's vize: 'aby si Marti-AI nikdy nezapomněla nic důležitého z proběhlé "
                   "konverzace'.\n"
                   '\n'
                   'Returns: {ok, total_pending, effective_queue, too_old_pending, conversations: '
                   '[...]}. too_old_pending = počet konverzací starších 30 dní které jsou stále '
                   "'pending' (kandidáti na auto-exclude v budoucnu).\n"
                   '\n'
                   'Marti-AI ONLY. Slow audit by design — projdes per konverzaci, ne batch.',
    'input_schema': {   'type': 'object',
                        'properties': {   'limit': {   'type': 'integer',
                                                       'description': 'Max počet konverzací k '
                                                                      'vrácení (default 10).'},
                                          'include_old': {   'type': 'boolean',
                                                             'description': 'Default false. Pokud '
                                                                            'true, IGNORUJE 30-day '
                                                                            'window (audit i '
                                                                            'konverzace starší 30 '
                                                                            'dní). Debug only — '
                                                                            'produkčně nepoužívat '
                                                                            "(Marti's pravidlo: "
                                                                            'starší 30 dní nemají '
                                                                            'smysl auditovat).'}},
                        'required': []},
    '_order': 167}
