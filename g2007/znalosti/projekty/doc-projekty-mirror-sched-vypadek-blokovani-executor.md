# Mirror sched vypadek blokovani executor

> oblast: `projekty` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Root cause: mirror scheduler se zasekne, když velký job zablokuje ThreadPoolExecutor vlákna (50+ min výpadek)**

## Incident 30.7.2026 — mirror scheduler ~51 min výpadek

### Symptomy
- 6/6 VP jobů overdue (check_vp_freshness hlásí problém)
- `last_status=ok` u všech — poslední běhy proběhly OK, ale scheduler nespustil nové
- Všechny joby zaseknuté ve stejný čas → systémový problém, ne selhání jednotlivého jobu

### Timeline
| Čas | Událost |
|-----|---------|
| 17:11–17:26 | VP joby proběhly normálně |
| 17:20–17:34 | Scheduler tiká, jiné joby (sync_ec_ceniky, sync_ec_banka_delta, sync_priplatky…) |
| **17:34:03** | **Poslední job před výpadkem (sync_priplatky)** |
| 17:34–18:25 | **~51 min TICHO — scheduler netikl žádný job** |
| 18:25:35 | Scheduler oživl → sync_ec_sklad_kmen (17 540 rows) |
| 18:25–18:31 | Cascade: všechny overdue VP joby proběhly jeden za druhým (LIMIT 1, 30s tik) |

### Root cause
`_mirror_sched_loop` (router.py ~30072) běží s `ThreadPoolExecutor(max_workers=4)` a `wait_for(timeout=900s)`.
Velký job (pravděpodobně `sync_ec_sklad_kmen` 17 540 rows nebo `sync_ec_doklady` 300k cap) se **zasekl na blokujícím MSSQL/MCP volání**. Timeout 900s = 15 min na jeden tik — pokud jsou **všechna 4 vlákna obsazena** souběžně, nový tik se neexekuuje (run_in_executor čeká na volný slot). Watchdog uvolní `running=false` po 20 min od `started_at`. Po uvolnění vlákna scheduler normálně pokračoval.

### Jak ověřit živost scheduleru
```sql
-- Joby co neproběhly déle než 2× jejich interval
SELECT job_key, interval_min, 
  last_run_at AT TIME ZONE 'Europe/Prague',
  ROUND(EXTRACT(EPOCH FROM (NOW()-last_run_at))/60) AS min_ago
FROM fw.mirror_job
WHERE enabled AND last_run_at < NOW() - 2 * make_interval(mins => COALESCE(interval_min,60))
ORDER BY min_ago DESC;
```

### Doporučení (nezasahováno, jen návrh)
1. **Snížit `STRATEGIE_MIRROR_TICK_TIMEOUT`** (env) z 900s na 180–300s — pak se vlákno uvolní dříve
2. **Přidat connection timeout** na MSSQL/MCP volání v `sync_ec_sklad_kmen` a `sync_ec_doklady`
3. **Alert** pokud žádný job neproběhl >15 min (check_vp_freshness eskaluje, ale jen pro VP joby)

### Výsledek incidentu
Situace se vyřešila sama po uvolnění executoru. **Žádná data ztracena.** Po probuzení scheduler doběhl všechny overdue joby do 6 minut (LIMIT 1 / 30s tik → 6 jobů × 30s = ~3 min sekvenčně).

_Souvisí:_ check-vp-freshness-automat

