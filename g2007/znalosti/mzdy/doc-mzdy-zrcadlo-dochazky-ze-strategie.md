# ZRCADLO DOCHAZKY (att_day_summary) SE PLNI ZE STRATEGIE, NE Z CENTRALY (Peta + Kristy + Tynka 6.8.2026)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Zrcadlo dochazky se plni ze STRATEGIE, ne z Centraly

**Peta + Kristy + Tynka, 6. 8. 2026. Zavazne.**

Kristy: *"tabulku muzeme pouzit, to je ok, ale musi byt plnena daty ze strategie."*
Tynka: *"kladla jsem duraz na to, aby to bylo ze STRATEGIE."*

## Co bylo spatne

`tenant.att_day_summary` je NASE tabulka, ale plnila se **z Centraly**
(`EC_Dochazka_SumaDen`) - v kodu stalo doslova *"EC = zdroj pravdy"* (Marti 28.6.2026).
V Centrale uz ale cervencova dochazka vetsinou NENI (lide se tam nepichali) a nase
opravy tam nedotecou. Kristy s C24 proto 3. 8. udelaly prepocet z nasi dochazky
(`att_day_summary_recompute`, tlacitko **Prepocitat** v /payroll), jenze **generovani
mezd zrcadlo pokazde prepsalo zpatky z Centraly**.

**Rozsah k 6.8.2026:** hodiny se lisily u **39 lidi o 84,8 h**, absence u **10 lidi**.
Nejhorsi Zeman (40): v Centrale 24 h dovolene, u nas 104 h.

Ve zdi `docs/team/Peta26_mzdy.md` az do 6.8. stalo, ze *"zrcadlo se do mezd nepouziva"* -
to NEBYLA pravda a je to opraveno.

## Co na tom zrcadle visi

| co | skript |
|---|---|
| **dovolena do Heliosu** (slozka 211) | `mzdy_absence_rows` - dny z att_entry, ale HODINY dovolene ze zrcadla (Peta 8.7.2026) |
| **Landmark nahrady** (obleceni 794, home office 795, korekce 432) | `mzdy_benefity_apply` - dny z att_entry, ale ABSENCE ze zrcadla |
| **nahrazene volno** v kaskade prescasu | `mzdy_loajalita_rows` |

Prescas a stravenky ctou nasi dochazku primo, tech se to netykalo.

## Co se 6.8.2026 zmenilo

Zrcadlo se nove plni **`att_day_summary_recompute`** (prepocet z `tenant.att_entry`)
na VSECH cestach:

| cesta | stav |
|---|---|
| generovani mezd - `mzdy_refresh_zrcadla` (g2007.python) | prepnuto |
| generovani mezd - `_mzdy_refresh_zrcadla` (router.py, z `_mzdy_full_run`) | prepnuto |
| `@@DOCHSUM <rok> <mesic>` (most) | prepnuto |
| Ridici pult -> "sync_ec_dochazka_sumaden" | prepnuto (delegat `_ec_dochsum_ze_strategie`) |
| Migrace hub -> Dochazka i Mzdy | navod prepsan na "UZ NESPOUSTET" |
| Ridici pult -> "sync_sumaden_2026_05" | **ZUSTAVA Z CENTRALY** |

`sync_finance_zakazek` a `sync_odmeny_from_ec` v refreshi zustaly, ale POZOR - obe
cesty do mezd jsou davno VYPNUTE (premie ze zakazek 5.8. Peta, odmeny 10.7. Marti),
takze plni tabulky, ktere do mzdy nevstupuji. Jsou to zbytky, ne "legitimni zrcadla".

## KVETEN 2026 = VYJIMKA

Peta 6.8.2026: *"ten kveten ne, ten je z centraly spravne"* - kvetnove mzdy se delaly
jeste z Centraly. **05/2026 i 06/2026 jsou proto v seznamu ZMRAZENYCH mesicu** primo v
`att_day_summary_recompute` (`FROZEN`) - prepocet je odmitne i pri rucnim spusteni.
Overeno zive: `@@DOCHSUM 2026 5` vrati *"mesic 05/2026 je zmrazeny (mzdy) - prepocet
odmitnut"*. Dalsi uzavreny mesic = pridat do FROZEN.

## CO SE PRO MZDY CTE Z CENTRALY (stav k 6.8.2026)

Jedine dve veci:

1. **Mzdove podminky a hodinova sazba** - `tenant.helios_wage_snapshot`, snimek
   z `EC_FinZamPodminky` (plni se RUCNI akci, ne automatem)
2. **Kveten 2026** - viz vyse

**Vsechno ostatni mzdy ctou ze STRATEGIE.**

### NEPLEST "odkud mzdy ctou" s "jak se tam data dostala" (Peta 6.8.2026)

Peta: *"tobe je ale jedno, odkud se to do S dostalo, pro mzdy je mas brat ze
strategie - vcera jsme si to jasne rekli."*

**Priplatky a srazky** mzdy berou z `tenant.wage_movement`, **tedy ze STRATEGIE**.
Je jedno, ze tam cast prisla Jirkovym importem z Centraly (`import_src='EC_PRIPL'`)
a cast jsme 5.8.2026 doplnili rucne z Excelu (65 radku). Zdroj pro mzdy = nase
tabulka, ne Centrala. Stejne tak dochazka: nezalezi, jestli clovek pichnul na tabletu
nebo to nekdo opravil ve Sprave dochazky - pro mzdy je zdroj `att_entry`.

## Overeno na cervencovych vyplatnicich (6.8.2026, po ciste vode)

- **Zeman (EC 40):** slozka 211 Dovolena = **104 h / 13 dnu / 38 178 Kc** (pred opravou
  by slo 24 h). Nahrada obleceni 1 090 Kc - spravne zkracena vyssi absenci.
- **Civis (ES 522):** dovolena 48 h / 6 dnu, prescasovy priplatek 651 = 108 Kc.
- Absence v zrcadle sedi s nasi dochazkou **u vsech lidi**.
- Hodiny se lisi u 9 lidi a je to spravne: 5 ma "plny fond bez dochazky"
  (Marti Pasek EC 2 + ES 41, Mozer 47, Vlkova 361, Senft 374), 4 maji
  **nepritomnost OSVC**, ktera se do fondu nepocita (Lev 371, Honal 370,
  Vorisek 327, Erhard 372).

## Souvisejici

- G2007 `doc-mzdy-vstupy-ze-strategie`, `doc-dochazka-att-day-summary-z-att-entry`
- pojistky `podklad-hodiny-ze-strategie`, `mzdy-hodiny-ze-strategie`, `mzdy-vstupy-ze-strategie`
- zed `docs/team/Peta26_mzdy.md`

