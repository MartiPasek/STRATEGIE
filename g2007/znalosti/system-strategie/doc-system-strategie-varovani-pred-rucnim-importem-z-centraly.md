# Rucni spusteni importu ze stare Centraly ted varuje a chce potvrzeni (25.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Rucni spusteni importu ze stare Centraly varuje a chce potvrzeni

Zadal **Jirka Honomichl 25. 8. 2026**, schvalila **Marti-AI (msg 13706)**, postavil Claude-28. Commity `aa186a32` + `c9e674af` + `5232fcc7`.

## Vychozi stav (overeno v kodu i v datech 25.8.2026)

Automaticka hlidka `_maybe_sync_ec_dochazka` je **pozastavena od 30. 7. 2026** (`return` hned na zacatku funkce). Potvrzeno i daty: dochazka se zdrojem `centrala1` naposledy pribyla **11. 8. 2026**, rozpad zakazek **5. 8. 2026**.

**Rucne se ale import porad spustit dal, a to ctyrmi dvermi:**

| Dvere | Co spusti | Stav |
|---|---|---|
| ERP tlacitko v Ops akcich `att_resync_full` | cisty re-import dochazky od ledna | zive, jedno kliknuti |
| `@@VYRWSYNC` (most) | `sync_vyroba_work_ec` — rozpad zakazek | zive |
| `@@DOCHRESYNC <od> <do>` (most) | `sync_ec_dochazka_recent` s `wipe=True` | zive |
| `@@DOCHAZKA <rok> <mesic>` (most) | `_sync_dochazka_ec` | **uz drive zazdeno** (C24/Kristy 31.7.2026) |

## Presny dopad (proto ta varovani)

`att_resync_full` jede po mesicich od 1. 1. 2026 do vcerejska a kazdy mesic vola `sync_ec_dochazka_recent` s `wipe=True`. Wipe dela:

```
DELETE FROM tenant.att_entry
WHERE tenant_id=2 AND source_system='centrala1'
  AND COALESCE(local_lock,false)=false AND entry_date v rozsahu
```

- **Zamek uzavreneho obdobi (`tenant.att_period_lock`) tato funkce NEKONTROLUJE VUBEC** — 0 vyskytu v jejim zdroji. Sahne tedy i do uzavrenych mesicu (uzavreno leden az cervenec 2026).
- **Rucne opravene radky (`local_lock`) jsou chranene** — pojistku pridal Claude-28 30. 7. 2026, schvalila Marti-AI msg 11818.
- Merenu 25. 8. 2026: v sazce **20 436 zaznamu u 66 lidi**, chranenych **38 u 12 lidi**.
- **U rozpadu zakazek (`sync_vyroba_work_ec`) obdobna ochrana NEEXISTUJE** — `UPDATE … SET zakazka_ref, datum, od, konec, hodiny … WHERE source_system='centrala1' AND source_id=:sid` prepise rucni opravu casu i zakazky bez podminky. Priznak "rucne upraveno" v systemu neni (0 vyskytu v datech i v kodu).
- Ve stare Centrale se **od 11. 8. 2026 nepicha**, takze import by dnes prinesl zastaraly stav.

**Overena vyvracena obava:** re-import by NEZRUSIL uklid cervna od Kristy z 20. 8. Tech 53 odstavenych hlavicek ma `source_system` prazdny, ne `centrala1`, takze je wipe nemaze.

## Co se postavilo

**A) ERP tlacitko.** `_OPS_ACTIONS` (router.py) ma nove volitelne pole **`warning`**. Kdyz existuje, `deploy_button.js` ve funkci `_opsConfirm` ukaze **jeho text** misto obecne vety "Spusti pojmenovanou ops akci… zapise se do auditu", a potvrzovaci tlacitko je **cervene** s popiskem "Ano, pokracovat" (misto zeleneho "Nasadit"). Kdyz `warning` chybi, chovani je **presne jako driv** — overeno na zivem `/api/v1/erp/ops/actions`, kde vsech 15 ostatnich akci ma `warning: null`. Pole se posila z obou endpointu (`/ops/actions` i `/app/ops/actions`).

**B) Prikazy mostu.** Sdilena funkce **`_import_centrala_gate(sql, nazev, dopad)`** v router.py. V mostu nejde vyskocit dialog, takze ekvivalent je: **bez slova `POTVRZUJI` se import NESPUSTI** a vrati se varovani s dopadem a navodem. Chraneny jsou `@@VYRWSYNC` a `@@DOCHRESYNC`.

- **Nahled `@@VYRWSYNC dry` varovani nepodleha** — nic nezapisuje, takze projde rovnou.
- **Text varovani MUSI jit v poli `error`.** Kdyz se posle pod vlastnim nazvem (`varovani`), most zobrazi jen *"neznama chyba"* a clovek se text vubec nedozvi. Overeno naostro.

## Jak se to overilo (ne jen ctenim kodu)

- `@@VYRWSYNC 2030-01-01 2030-01-02` -> varovani, import se nespustil
- `@@DOCHRESYNC 2030-01-01 2030-01-02` -> varovani, import se nespustil
- `@@VYRWSYNC 2030-01-01 2030-01-02 dry` -> **proslo**, nahled nerozbity
- zive `/api/v1/erp/ops/actions` -> `att_resync_full` nese warning, ostatnich 15 akci `null`
- zive `/static/deploy_button.js` -> obsahuje `a.warning`

Rozsah v budoucnosti (rok 2030) byl zvolen zamerne: kdyby pojistka nefungovala, import by za to obdobi nenasel zadna data a nic by nezpusobil.

## Pozor pri pristi uprave

Cisla v textech varovani (20 436 / 66 lidi / 38 / 12) jsou **zmerena 25. 8. 2026 a jsou orientacni**, ne pocitana zive. Je to v textu vyslovne receno. Kdyz se budou aktualizovat, zmer je znovu.

Pri stavbe teto zmeny jsem naletel na past s dekoratorem, ktera **rozbila cely most** — viz [[doc-system-strategie-nova-funkce-pod-dekoratorem-rozbije-endpoint]].

Souvisi: [[doc-dochazka-skupiny-kategorie-a-skryta-vazba-na-mzdy]]

