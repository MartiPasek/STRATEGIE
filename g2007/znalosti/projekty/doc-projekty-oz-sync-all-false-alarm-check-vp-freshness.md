# Oz sync all false alarm check vp freshness

> oblast: `projekty` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**check_vp_freshness hlásí oz_sync_all jako problém, přestože job normálně běží ~30 min**

## oz_sync_all — false alarm v check_vp_freshness (1.9.2026)

### Co se stalo
`check_vp_freshness` eskaloval `oz_sync_all` jako problém (stav=běží, 33 min od last_run_at).
L0 ani L1 (Haiku) to nevyřešily — chyběl kontext, že 30 min je normální délka tohoto jobu.

### Skutečný stav (ověřeno z fw.mirror_job)
- Job se spustil v 09:02, dokončil v 09:35 → trvání ~33 min = normál
- last_status=ok, last_rows=128 780, last_done=true
- interval_min=30, overdue=False po celou dobu
- Scheduler byl živý (ostatních 5 VP jobů proběhlo normálně)

### Root cause alarmu
`check_vp_freshness` vyhodnocuje `running=true` jako "problém", bez ohledu na `overdue`.
Správná logika: `running=true` + `overdue=False` = probíhá normálně, NEPŘIDÁVAT do problémů.

### Normální trvání oz_sync_all
~30 min (doloženo z G2007 doc-vyroba-vyhodnoceni-zakazek-stav-4-8-2026: behy 08:24, 08:56, 09:30 a dnes 09:02–09:35).
Ostatní VP joby trvají 9–10 min — oz_sync_all je výrazně delší kvůli objemu (128k+ řádků).

### Doporučená oprava check_vp_freshness
Přidat podmínku: job se reportuje jako problém pouze pokud `overdue=True` NEBO (`running=True` AND trvání > 2× průměr).
Pouhý `running=True` bez `overdue` = informace, ne alarm.

_Souvisí:_ doc-vyroba-vyhodnoceni-zakazek-stav-4-8-2026, doc-projekty-mirror-sched-vypadek-blokovani-executor

