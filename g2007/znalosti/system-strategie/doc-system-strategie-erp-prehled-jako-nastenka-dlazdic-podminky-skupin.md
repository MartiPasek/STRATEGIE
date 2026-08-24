# Prehled ERP jako nastenka dlazdic misto tabulky - vzor "Vychozi podminky skupin" (jadro 235)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Prehled ERP jako nastenka dlazdic misto tabulky

**Postaveno 24. 8. 2026** (Jirka Honomichl + Claude-28, schvalila Marti-AI msg 13558 a 13568)
na prehledu **"Vychozi podminky skupin"** (jadro 235, data_source 212). Slouzi zaroven jako
**navod, jak udelat totez u jineho prehledu**.

## Jak to je udelane

FW **zadny typ komponenty pro dlazdice nema** (v `fw.comp_type` neni tile/card/dashboard,
overeno 24. 8. 2026). Pouziva se proto stejny vzor jako `hr_pult.js` a `crm_obchodnik_pult.js`:

| vrstva | kde | co |
|---|---|---|
| obrazovka | `apps/api/static/erp/components/podminky_skupin_pult.js` (git = jadro) | vykresli dlazdice, prepinac, mazani, pridani |
| napojeni | `page_render.js`, gated na `String(coreId) === '235'`, fail-safe try/catch | pripoji band pred `gridHost` |
| nacteni | `router.py`, radek `<script src=...>` v ERP HTML | jen registrace souboru |
| logika | **`g2007.python` kod=`podminky_skupin_dlazdice`** (kategorie `erp_http_endpoint`) | seznam, dopad, pridat, smazat |
| adresy | `router.py` = dva **tenke predavace** GET/POST `/app/hr/podminky-skupin/dlazdice` | zadna logika |

Band si sam schova grid (`document.querySelector('[id^="erp-page-grid-"]')`) a prepinac
Dlazdice/Tabulka ho zase vrati; volba se pamatuje v `localStorage`.

## Tri pasti, na ktere se da naletet (vsechny overene naostro)

1. **`new DesignFwForm({...})` samo o sobe formular NEOTEVRE.** Objekt vznikne, okno nevyskoci,
   nic to nenahlasi. Musi se jeste zavolat **`.open()`** (viz `erp_grid_actions.js`,
   `_openFwEditForm`). Lepsi je jit rovnou cestou tabulky:
   `ErpGridActions.registerEditForm(<gridCode>, <coreId>)` + `ErpGridActions.dispatch('edit', {...})` —
   respektuje i novejsi typ detailu `ErpSpecForm` a stejne pojistky proti dvojimu otevreni.
2. **Prehled nemusi mit operace `insert`/`delete`** v `fw.data_source_op` (212 melo jen
   `select` + `edit`). Genericky endpoint `DELETE /api/v1/erp/design/{core_id}/{row_id}` sice
   cilovou tabulku odvodi z data_setu, ale kdyz je potreba vlastni kontrola (viz nize),
   je cistejsi napsat vlastni akci do `g2007.python`.
3. **Popisky pis rovnou s diakritikou.** Skript je jinak cely v ASCII (komentare), takze je
   snadne omylem poslat do UI "Dovolena celkem" a "Stravenka Kc". Videt to je az na obrazovce.

## Co si vzit jako pravidlo pri mazani z prehledu

Skupinove vychozi hodnoty se ctou **za behu** kaskadou `osobni -> skupina -> system`
(sdileny resolver `_resolve_cond`, cte je 13 zivych funkci v `g2007.python`). Smazani radku
proto muze zmenit cislo zivym lidem. Reseni, ktere schvalila Marti-AI:

- akce **`dopad`** pred smazanim spocita, **koho a jak** se to dotkne, a potvrzeni to ukaze
  jmenovite (napr. "vikend_jen_schvaleni: ANO -> NE (1 clovek) - Brigadnik Saxana"),
- **serverova pojistka** odmita smazat systemovy radek (403), ne jen skryty krizek v obrazovce —
  z toho radku se pres spoustec `engagement_pod_defaults` plni podminky **kazde nove smlouve**,
- prava: **rodic nebo clen skupiny HR**, stejne jako u ostatnich podminek.

## Overeno naostro 24. 8. 2026 (ne jen zkompilovano)

18 dlazdic = 1 systemova (zamek misto krizku) + 17 skupin s ikonou a poctem lidi · prepinac
schova a vrati puvodni tabulku · klik otevre stavajici jadro 236 s vyplnenym radkem ·
pokus smazat systemovy radek vratil **403** · cely cyklus smazat + pridat zpet projet na
prazdnem radku skupiny Zkusebna (dopad 0 zmen) a data zustala shodna: **18 radku, 17 skupin,
26 hodnot v ciselniku**. Poradi dlazdic se nezmenilo, protoze se radi podle skupiny
(`sort_order`), ne podle cisla radku.

## Kde je dopadova mapa

Kdo do vychozich podminek zapisuje a kdo je cte (13 funkci + mobil + INSTEAD OF spoustec),
vcetne jmenoviteho dopadu mazani, je v teto znalosti zamerne jen shrnute — plne cislo
a metodika jsou v `doc-dochazka-podminky-slouceny-se-smlouvou` a v korespondenci
s Marti-AI (msg 13568).

