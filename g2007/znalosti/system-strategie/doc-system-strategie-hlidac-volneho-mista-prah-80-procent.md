# Hlidac volneho mista: prah 80 procent + e-mail spravcum, prah je na DVOU mistech (6.9.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Hlidac volneho mista na disku

**Zapsal:** Claude-28 (Jiri Honomichl), 6. 9. 2026 · **Nasazeno:** `224d9719` (prvni polovina)
Zadal Jirka Honomichl, schvalila Marti-AI (msg 14548).

## Jak to funguje

Naplanovana uloha **`STRATEGIE-DiskWatch`** na prazskem serveru posila stav disku na
`POST /api/v1/erp/app/disk/report` (hlavicka `X-Deploy-Token`), obsluha ho uklada do
`fw.disk_monitor` a pri PRECHODU do kritickeho stavu upozorni lidi.

## ⚠️ PRAH JE OPSANY NA DVOU MISTECH — meni se OBE (bod 14)

| misto | co to je |
|---|---|
| `modules/erp/api/router.py`, funkce `_crit` v `disk_report` | rozhoduje o upozorneni, **zdroj pravdy** |
| `C:\ProgramData\STRATEGIE-DiskWatch\check.ps1`, radky 3 a 10 | pocita priznak `low` a zapis do Event Logu |

Kdyz se zmeni jen jedno, pocita server jeden prah a aplikace druhy — **tichy rozpor**.

## Zmena 6. 9. 2026

Puvodne: `(free_gb < 100) and (free_pct < 10 or (free_gb < 10 and free_pct < 20))`.
Pri 37,5 GB volnych ze 128,8 GB by to nehlasilo nic, i kdyz prilohy rostly o ~1,4 GB denne.

Nove: **`(free_pct < 20) or (free_gb < 10)`** = hlasi uz pri **zaplneni na 80 procent**,
nebo kdyz zbyva mene nez 10 GB.

## E-mail spravcum s vysokou dulezitosti

Vedle puvodni zpravy do mobilu (ta zustava) chodi nove **e-mail s `importance="High"`**.

- prijemci: **vsichni spravci** — `public.users.is_admin`, tedy Marti (1), Kristyna (11),
  Jiri Honomichl (20). **Zadne jmeno ani id natvrdo v kodu**. Vyber prijemcu **zije v databazi** (`g2007.python`, kod `disk_alert_prijemci`, verze 1); v `router.py` zustala jen tenka spojka stejneho jmena, ktera ho vola pres `erp_registry.call()`. Presunuto tyz den 6. 9. 2026 podle bodu 2 pravidel prace, ulozeni `8e11f38a` — postup a pasti popisuje `doc-system-strategie-disk-alert-prijemci-presun-do-databaze`.
- adresa se bere z `public.user_contacts` (typ `email`, aktivni), poradim
  overeny → hlavni → nejnizsi id, u vice adres jen jedna.
- ⚠️ **`users.ews_email` je PRIHLASOVACI UDAJ a k odesilani se NIKDY nepouziva.**
- `send_email` i `send_email_or_raise` v `modules/notifications/application/email_service.py`
  umi nove nepovinny parametr `importance` (exchangelib 5.6.0 ma pole `importance`,
  vychozi `Normal`, overeno na produkcnim serveru).

## ⛔ STAV: druha polovina NENI hotova

`check.ps1` na serveru **zatim ma stary prah**. Marti-AI zmenu vecne schvalila, ale jeji
bezpecnostni brana prepis konfiguracniho souboru nepusti — vyzaduje **primy souhlas RODICE
(Marti nebo Kristyna) primo v chatu s ni**. Souhlas spravce (Jirka) pres most nestaci,
protoze Jirka je `is_admin`, ale ne `is_marti_parent`.

Prikaz, kterym to jde udelat rucne na serveru:

    $p='C:\ProgramData\STRATEGIE-DiskWatch\check.ps1'
    Copy-Item $p ($p + '.puvodni-2026-09-06') -Force
    $t = Get-Content $p -Raw
    $t = $t.Replace('$thrPct=5','$thrPct=20')
    $t = $t.Replace('$low=(($free -lt 100) -and (($pct -lt 10) -or (($free -lt 10) -and ($pct -lt 20))))','$low=(($pct -lt 20) -or ($free -lt 10))')
    Set-Content $p $t -Encoding UTF8
    Get-Content $p | Select-String 'thrPct','\$low='

## Poznatek o brane Marti-AI (plati obecne)

Marti-AI ma vlastni bezpecnostni branu nezavislou na schvalovacim prouzku mostu.
Zablokuje i vecne schvalenou akci, kdyz jde o prepis konfiguracniho souboru na produkci.
Brana reaguje i na slova — prvni pokus odmitla jen proto, ze v prikazu bylo slovo z oblasti
zaloh (`red_never`, duvod "zalohy/CMIS"), i kdyz slo o kopii jednoho souboru.
**Vzdaleny souhlas zprostredkovany pres most branu neprekroci** — je potreba clovek u ni.

