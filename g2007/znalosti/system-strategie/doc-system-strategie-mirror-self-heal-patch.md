# Mirror scheduler self-heal (PENDING nasazeni) - presny patch + jak nasadit ciste

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Mirror scheduler self-heal - hotovy patch, ceka na CISTE nasazeni (C23, 31.7.2026)

## Proc
Mirror scheduler loop (`_mirror_sched_loop` v modules/erp/api/router.py) obcas po
deploy-restartu tise neozije / umre -> mirror joby stoji i 10 h, zatimco automaty
bezi dal (naposledy 30.7. 22:40, mrtvy ~10 h). Fix: automat loop (spolehlivy, jede
na primaru) pri kazdem tiku zkontroluje mirror loop; kdyz je mrtvy, znovu ho nahodi
a zaloguje duvod smrti.

## Patch A - modules/erp/api/router.py
Vloz NOVOU funkci MEZI `_mirror_sched_start()` a `_mirror_sched_stop_now()`
(kotva: hned za telem `def _mirror_sched_start(): ...`, PRED `def _mirror_sched_stop_now():`):

def _mirror_sched_ensure_alive():
    """Self-heal dozor nad mirror schedulerem (C23 31.7.). Mirror loop task obcas
    tise umre / nenaskoci po deploy-restartu -> mirror joby stoji i 10 h. Automat
    loop vola tuhle funkci kazdy tik; kdyz je task mrtvy, nahodi ho a zaloguje duvod."""
    t = _MIRROR_SCHED_TASK[0]
    if t is not None and not t.done():
        return
    reason = "task=None (nenaskocil)"
    if t is not None:
        if t.cancelled():
            reason = "cancelled"
        else:
            try:
                _exc = t.exception()
                reason = ("vyjimka: %r" % _exc) if _exc else ("loop vypadl (STOP=%s)" % _MIRROR_SCHED_STOP[0])
            except Exception:  # noqa: BLE001
                reason = "neznamy (exception() selhal)"
    logger.warning("[mirror_sched] SELF-HEAL: loop byl mrtvy (%s) -> nahazuji znovu", reason)
    _mirror_sched_start()

## Patch B - modules/erp/api/automat.py
Uvnitr `_automat_sched_loop`, HNED za `if _SCHED_STOP[0]: break` (a PRED `loop = _aio.get_event_loop()`):

            try:
                from modules.erp.api.router import _mirror_sched_ensure_alive
                _mirror_sched_ensure_alive()
            except Exception as _me:  # noqa: BLE001
                _log.warning("[automat_sched] mirror ensure-alive selhal: %s", _me)

## Jak nasadit CISTE (dulezite - lekce z 31.7. incidentu)
Lokal EC-Martin (D:\Projekty\STRATEGIE = device most) je ZAMOTANY: diverguje od
origin/main o stary spatny commit ebf5d7d78 (smazal ~1100 r. priplatku) + revert
a69a86fd + hromada WIP (tool_registry refactor...). Pres most git-write NEJDE:
9p mount zakazuje unlink -> reset --hard neprojde (181 souboru by se muselo smazat);
navic most nema sit (fetch = 403 proxy). Deploy z tohohle lokalu je NEBEZPECNY -
rebase by prehral ebf5d7d78 a mohl znovu smazat priplatky.

Nasadit smi jen operator z CISTEHO checkoutu (realny Windows shell + sit + pravo mazat):
  1) git fetch origin && git reset --hard origin/main   (real origin HEAD k 31.7. ~ 086880dcd)
  2) aplikuj Patch A + B (male chirurgicke edity)
  3) py_compile modules/erp/api/router.py modules/erp/api/automat.py
  4) git add ty 2 soubory -> commit -> push -> POST /deploy/now (nebo deploy lane z cisteho lokalu)
  5) over: po pristim deploy-restartu smi byt v logu API "[mirror_sched] SELF-HEAL: ..."
     a mirror joby (fw.mirror_job) jedou. Bez self-heal by po nahodilem restartu stály.

