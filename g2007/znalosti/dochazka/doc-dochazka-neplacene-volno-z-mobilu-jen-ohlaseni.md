# Neplacené volno z mobilu = jen ohlášení vedoucímu + písemná žádost, do docházky nic

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Neplacené volno z mobilu — jen ohlášení, do docházky nic

**27. 8. 2026, Peťa + C26.** Peťa: *„neplacené volno bych udělala stejně jako nemoc a OČR,
tedy info pro vedoucího, a mělo by to jít do toho přehledu, který jsme stavěli včera —
s tím, že zaměstnanci když to vybere, by to mělo napsat, že musí dodat písemnou žádost
o neplacené volno."*

## Pravidlo
Neplacené volno (`unpaid`) nahlášené z mobilu se chová **stejně jako nemoc, OČR a lékař**
(viz `doc-dochazka-mobil-nemoc-ocr-lekar-jen-info-vedoucimu`):
- do `att_entry` ani do `att_absence_request` **nevznikne NIC**,
- vedoucí dostane jen informaci na vědomí,
- **navíc oproti nemoci a OČR**: v hlášce se říká, že musí přijít **PÍSEMNÁ ŽÁDOST**
  o neplacené volno. Bez ní se nezapíše nic — zapisuje se ručně ve Správě docházky.

Do Správy docházky se ohlášení propíše jen do záložky **🧑‍⚕️ Ohlášení nepřítomnosti**
(dřív „Ohlášení lékař / nemoc / OČR", přejmenováno 27. 8.), a to jen ke čtení.

## Kde je to udělané
Všechny **tři** mobilní vstupy (kdo opraví jen jeden, nechá díru ve dvou zbylých):

| Vstup | g2007.python | Změna |
|---|---|---|
| „Tady budu jinde" | `att_absence` | `"unpaid"` do seznamu typů, které `_upsert` nezapisuje; do textu vedoucímu se přidá věta o písemné žádosti |
| Žádost o nepřítomnost | `att_absence_request` | `"unpaid"` do info-only větve; věta v notifikaci i v `note` pro zaměstnance |
| „Je mi blbě, dnes nedorazím" | `att_announce` | totéž |

Dataset `dochazka.ohlaseni_zdravi_list` pozná i `Neplacené volno`.

**Do mobilu se sahat NEMUSELO.** `60_dochazka.js` (řádek ~1137) už umí obecně: když server
vrátí `info_only`, appka vypíše `r.note` ze serveru. Stačilo tedy rozšířit text na serveru.
Kdyby někdo chtěl větu ukázat **už při výběru položky** (před odesláním), to už by úprava
mobilu byla — vědomě neuděláno (27. 8. v mobilu stavěl Jirka/C28).

## Ověřeno
Čtením z DB, ne návratovkou: guard i hláška sedí ve všech třech skriptech
(`att_absence` 1×, `att_absence_request` 2×, `att_announce` 2×). Záložka v prohlížeči
se jmenuje „🧑‍⚕️ Ohlášení nepřítomnosti" a vrací data.

## Souvislosti a co zbývá
- **Sick day** má otevřený nález — na budoucí den se tiše ztratí, v datech nevznikne nic
  (`doc-dochazka-sickday-budouci-den-se-tise-ztrati`). Peťa 27. 8.: *„psali jsme Jirkovi,
  tak doufám, že to vyřeší, ať si nelezeme do zelí."* **NEŘEŠIT bez domluvy s ním.**
- **Home office** je hotový a hlídaný (`ho-ohlaseni-nepatri-do-oprav`,
  `ho-ohlaseni-z-mobilu-ma-znacku`, `dochazka-ho-nematerializovat`).
- **Dovolená** jde od 11. 8. přes žádost
  (`doc-dochazka-dovolena-tri-cesty-a-schvalovani-planu-11-8-2026`).
- **Zbývá bez vazby na ohlášení:** `sickday` a `osvc_absence` z „Tady budu jinde" pořád
  zapisují den rovnou, bez `source_id`. Zrušení v appce (`att_absence_cancel`) hledá den
  výhradně podle `source_system='absence_req' AND source_id`, takže tyhle dny nenajde a
  zůstanou viset. K 27. 8. je takových osiřelých dnů od července **12** (7× stará dovolená
  před opravou z 11. 8., 3× OSVČ, 2× sickday).

