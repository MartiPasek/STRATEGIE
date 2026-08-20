# Rucni korekce osobniho ohodnoceni (pokuty, srazky) DO MEZD PATRI - kod korekce_os_ohod_kultura, slozka 432

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Rucni korekce osobniho ohodnoceni (pokuty) DO MEZD PATRI

**Peta 5.8.2026, zavazne. Uz to neresit znovu.**

Peta: *"Valenta je real a musi probublat do mezd."*

## Odkud se priplatky a srazky beru do mezd

- **Zdroj pravdy pro mzdy = `tenant.wage_movement`** = prehled **"Priplatky a srazky (Praha)"**
  (jadro `mzdy.pripl_prehled`). Cte ho skript `mzdy_priplatky_rows` (g2007.python),
  volany z `mzdy_generuj`.
- **Zrcadlo Centraly `ec.pripl_srazky`** (prehled **"Priplatky a srazky"**, jadro
  `ec.pripl_srazky_prehled`) se do mezd **NEPOUZIVA VUBEC** - overeno 5.8.2026, ani jeden
  mzdovy skript se na nej neodkazuje. Je to jen zobrazovaci okno do stare Centraly.
  **Jeho synchronizace je vypnuta** (potvrdil Jirka), takze byva zastaraly - to na mzdy
  nema vliv.

## Tri druhy, ktere `mzdy_priplatky_rows` VYNECHAVA - a proc

Vyluceny jsou kody `nahrada_home_office`, `nahrada_obleceni`, `korekce_os_ohod`.
Duvod: pocita je **`mzdy_benefity_apply`** (Landmark) sam z dochazky - obleceni (slozka 794),
home office (795) a **kraceni** osobniho ohodnoceni podle neodpracovaneho fondu (432).
Kdyby sly i pres priplatky, byly by ve mzde dvakrat.

Stav 7/2026 - pod temito tremi kody je ve `wage_movement` **0 radku**, takze vyluceni dnes
nic realneho nevyhazuje (Landmark se uz dela jinak). Je to pojistka z doby rucniho zadavani.

## POZOR - rucni pokuty a srazky NEJSOU tim vylucenim dotcene

Rucni korekce (napr. pokuta) prichazi z Centraly pod **JINYM kodem druhu**:
**`korekce_os_ohod_kultura`** (typ 10 v Centrale, "Korekce osobniho ohodnoceni").
Tento kod **NENI na seznamu vylucenych**, ma mapovani na **mzdovou slozku 432**,
a proto do mezd **normalne projde**.

**Overeny priklad (5.8.2026, cervenec 2026)** - Valenta Martin, os. cislo 517, ES, HPP,
pokuta za rychlou jizdu **-750 Kc**, zdrojove ID z Centraly 20046. V `wage_movement`
druh `korekce_os_ohod_kultura`, stav `approved`. V mzdovem ledgeru
`tenant.zamestnanecky_zavazek` jako slozka **432**, castka **-750**, stav `v_mzde`.
Tedy skutecne probublal do mezd.

**Nezamenovat** `korekce_os_ohod` (Landmark kraceni, vyluceno) s
`korekce_os_ohod_kultura` (rucni korekce/pokuta, do mezd patri). Rozdil je jen v pripone
kodu a chyba se pozna az na vyplatnici.

## Gotcha pro pristi instanci

Druh polozky **neodvozuj z ceskeho nazvu v Excelu** ("Korekce osobniho ohodnoceni"), ale
z **kodu druhu v `tenant.wage_component_type`**. Claude-26 se 5.8.2026 takhle spletl a
zbytecne varoval Petu, ze se pokuta do mzdy nedostane - pritom uz tam byla.

