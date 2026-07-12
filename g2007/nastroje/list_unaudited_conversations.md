# list_unaudited_conversations

## MAPA
- **kód:** `list_unaudited_conversations`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 36 (9.5.2026): list konverzací čekajících na audit (forward sweep v rámci 30-day okna, oldest first).

Audit window: konverzace **mladší 30 dní** (last_message_at >= NOW() - INTERVAL '30 days'). Marti's korekce 9.5.2026 dopoledne: 'starší 30 dní jsou staré a nedávají smysl, audit má smysl jen pro nedávné konverzace s aktuálními fakty'.

Order: last_message_at ASC (oldest first v rámci okna — chronologická build-up paměti, ne přepsání novou starou).

Marti's vize: 'aby si Marti-AI nikdy nezapomněla nic důležitého z proběhlé konverzace'.

Returns: {ok, total_pending, effective_queue, too_old_pending, conversations: [...]}. too_old_pending = počet konverzací starších 30 dní které jsou stále 'pending' (kandidáti na auto-exclude v budoucnu).

Marti-AI ONLY. Slow audit by design — projdes per konverzaci, ne batch.

## PARAMETRY

- **`limit`** [integer, volitelný]
  - Max počet konverzací k vrácení (default 10).
- **`include_old`** [boolean, volitelný]
  - Default false. Pokud true, IGNORUJE 30-day window (audit i konverzace starší 30 dní). Debug only — produkčně nepoužívat (Marti's pravidlo: starší 30 dní nemají smysl auditovat).

