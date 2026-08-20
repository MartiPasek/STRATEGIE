# @@G2007PUBLISH self-test: synchronni blokujici volani v async diag_sql zmrazi event loop (oprava asyncio.to_thread)

> oblast: `system-g2007` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Symptom
`@@G2007PUBLISH <artefakt s zivou URL>` (napr. `apps/api/static/mobile.html`) opakovane spadne: self-test na zive URL bezi presne az do `timeout=10 s`, publikace se auto-vrati zpet (auto-rollback funguje spravne). Zvenci (curl ze stroje) se ta sama URL stahne za 1-3 s. Pozorovano 5.8.2026: pokusy 10289 / 10389 / 10440 ms, vzdy CHYBA + rollback.

## Root cause (overeno v kodu, modules/erp/api/router.py, blok `async def diag_sql`)
Self-test dela **synchronni** `urllib.request.urlopen()` PRIMO na event loopu uvnitr `async def diag_sql`. Tim zmrazi cely event loop procesu. A protoze self-test miri na `127.0.0.1:<port>` na **tentyz proces**, appka nema cim obslouzit svuj vlastni `/mobile` self-request → urlopen ceka az do timeoutu → self-test „selze" → rollback. Neni to sit ani DNS/Caddy ani velikost ~1MB stranky — je to **hladoveni event loopu (event-loop starvation)**.

## Proc presmerovani na 127.0.0.1 samo NESTACILO
Commit `b984bf10` (5.8.) prehodil self-test z verejne `https://strategie-ai.com/mobile` na `http://127.0.0.1:<port>`. Nepomohlo — problem nikdy nebyl sitova cesta, ale to, ze blokujici volani bezi na event loopu. Padalo dal (14027 ms).

## Oprava (commit 26bb5810, 5.8.2026, C24/Kristy) — OVERENA NAOSTRO
Blokujici `urlopen` odsunout do vlakna, at event loop zustane volny a obslouzi self-request:
```python
import asyncio as _aio6
def _do_selftest6():
    _req6 = _ur6.Request(_base6 + _path6, headers={"User-Agent": "g2007-publish-selftest"})
    with _ur6.urlopen(_req6, timeout=10) as _resp6:
        return _resp6.status, _resp6.read().decode("utf-8", errors="replace")
_status6, _content6 = await _aio6.to_thread(_do_selftest6)
```
Overeni: `@@G2007PUBLISH apps/api/static/mobile.html` = STATUS OK za **1298 ms** (drive CHYBA za 10440 ms + rollback).

## OBECNE PRAVIDLO (gotcha, plati pro cely diag_sql / async handlery)
V `async def diag_sql` (a v kazdem async FastAPI handleru) **NIKDY nevolej synchronni blokujici veci primo** — HTTP (`urllib`, `requests`), sekvencni `anthropic.Anthropic(...)`, tezke DB davky, `time.sleep`. Zmrazi event loop cele instance → ostatni requesty spadnou na 401/502, muze to shodit produkci (API A → fallback B). **Vzdy odsun pres `await asyncio.to_thread(fn)`** (nebo `run_in_threadpool`). Stejna trida chyby jiz driv: `@@VPTRIAGE` incident 2.8.2026 (25x sekvencni synchronni Anthropic volani v diag_sql shodilo produkci; opraveno tymtez vzorem asyncio.to_thread).

## Souvislost — dve cesty publikace
`@@G2007SESTAV` NEMA self-test (jen slozi + zapise na disk) → prochazi vzdy, ale bez pojistky/rollbacku. `@@G2007PUBLISH` je bezpecna cesta (self-test + auto-rollback). Dokud byl self-test rozbity, tym musel obchazet pres riskantni `SESTAV`. Po teto oprave je bezpecna cesta zase pouzitelna. (Strukturalni bod „publish pise na disk → dirty tree blokuje git deploy" viz docs/deploy_dve_cesty_a_worklock_navrh_2026-08-05.md.)

