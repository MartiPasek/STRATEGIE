# MZDY - VSTUPY SE BEROU ZE STRATEGIE, NE Z CENTRALY (Peta 5.8.2026, zavazne)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# ⭐ ZAVAZNE PRAVIDLO

Peta 5.8.2026: *"vetsina dochazky uz v cervenci v Centrale neni, proto nedava smysl se tam
na neco koukat."* Opravy dochazky i mzdovych podkladu se delaji ve STRATEGII a do Centraly
NEDOTECOU - kdo cte zrcadlo, pocita ze zastaralych dat.

## ODKUD SE CO BERE

| co | zdroj (vse tenant.*) |
|---|---|
| hodiny, fond, prescas | `att_den_hodiny` (nas vypocet nad att_entry, vc. oprav) |
| stravenky | `att_entry` podle **cisla cinnosti** (`ec_druh`), zaloha = typ zaznamu |
| pracovni dny a svatky | `firemni_kalendar` (doplnuje se sam pres `kalendar_zajisti`) |
| zaklad, osobni ohodnoceni | `helios_wage_snapshot` |
| **hodinova sazba prescasu** | `helios_wage_snapshot`, slozka `hod_sazba_prescas` = **HrHodsFK (S FK!)** |
| priplatky, odmeny, srazky | `wage_movement` |
| premie ze zakazek | priplatky -> slozka **651** (stara dochazkova cesta VYPNUTA 5.8.2026) |
| jednatele a DPP | `mzdy_rucni_slozka` |

⛔ **`tenant.att_day_summary` (zrcadlo Centraly) se do mezd NEPOUZIVA.**

## PROC (dukaz)

Svatos 7/2026: zrcadlo melo **123,85 h / 17 dnu**, nase dochazka **185,66 h / 23 dnu**.
Pri cteni zrcadla by prisel o 9,66 h prescasu, z toho 7,92 h ve svatek s koeficientem 2,00.
Stejne stravenky: pres zrcadlo vychazelo 35 lidi, z nasi dochazky 43 - lidem chybely dny,
ktere v Centrale nejsou.

## SAZBA PRESCASU - POZOR NA "S FK"

Pouziva se `HrHodsFK` (s firemni kulturou), NE `HrHodBezFK`. U 16 lidi se lisi
(napr. Veverka 442,53 vs 396,55). Ulozena presne na halere - sloupec `castka` byl kvuli tomu
zmenen z celociselneho na numeric(14,2) (pohled `v_wage_compare` se pri tom prevytvoril 1:1).

## KDE TO JE ZAPSANE

- hlavicka primo ve skriptu **`mzdy_generuj`** (vidi to kazdy, kdo ho otevre),
- pravidla pro cloveka: **`docs/team/Peta26_mzdy.md`** ("velka zed"),
- pojistka **`mzdy-vstupy-ze-strategie`** - spadne, kdyby nekdo vratil vypocet na zrcadlo.

