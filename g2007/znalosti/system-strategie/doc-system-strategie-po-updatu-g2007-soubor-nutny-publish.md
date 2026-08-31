# Doc system strategie po updatu g2007 soubor nutny publish

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Po přímém UPDATE do g2007.soubor je nutné zavolat @@G2007PUBLISH — jinak změna na disk nedojde**

# Po UPDATE do g2007.soubor je nutný @@G2007PUBLISH

**Datum:** 31.8.2026 · **Zdroj:** incident C28 + Jirka

## Past, do které lze spadnout

Při přímém `UPDATE g2007.soubor SET obsah=... WHERE kod=...` (přes most nebo SQL) se změna uloží do DB, ale **na disk serveru nedojde automaticky**. Aplikace čte statické soubory z disku, ne z DB za běhu.

Bez publish:
- Změna je v DB, ale soubor na disku je stará verze
- Deploy (`git pull`) skončí `already_up_to_date` — nemá co stáhnout, restart nezpůsobí
- `/api/v1/erp/restart-api` by soubor aktualizoval (materializace při startu), ale:
  - endpoint chce `is_marti_parent` (Jirka jako admin dostane 403)
  - zbytečný restart jen kvůli zapomenutému publish je špatná praxe

## Správný postup

Po každém `UPDATE g2007.soubor`:
```
@@G2007PUBLISH <kod>
```
Příkaz zapíše soubor na disk **okamžitě** bez restartu API. Materializace při startu je jen záchranná síť pro případ, že publish selhal nebo byl přeskočen — není to běžná cesta.

## Ověření

Po publish zkontroluj timestamp souboru na disku nebo načti endpoint — změna musí být živá okamžitě, bez čekání na restart.

## Kontext incidentu 31.8.2026

C28 opravil pretékání (113 → 0 px) přes UPDATE do g2007.soubor, zapomněl zavolat @@G2007PUBLISH. Oprava tři dny nefungovala. Pokus o restart přes most skončil restartem zálohy v Plzni (EC-SERVER2:8080) místo produkce (EUR-APP-1P:8002) — viz doc-marti-ai-dva-nastroje-dva-servery. Po publish ověřeno ve všech pěti pohledech.

_Souvisí:_ doc-system-g2007-migrace-python-soubor-stav-2026-08-01, doc-marti-ai-dva-nastroje-dva-servery

