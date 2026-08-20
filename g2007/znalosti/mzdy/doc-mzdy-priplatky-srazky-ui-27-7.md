# Priplatky a srazky - UI uprava 27.7.2026 (popisky dle Centraly, cislo+nazev, zamek na cteni) + 4 gotchy frameworku

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Priplatky a srazky (Mzdy) - UI uprava 27. 7. 2026

> oblast: mzdy - Claude-28 (Jirka). Navazuje na [[doc-mzdy-priplatky-srazky]] (V3.0, stav k 22.7.).
> Podnet: Peta Safrankova poslala 2 snimky ze stare Centraly misto textove odpovedi.

## Co se zmenilo (nasazeno, overeno v prohlizeci)
- **Popisky poli v jadru dle Centraly** (comp_def 1283-1299): "Druh odmeny", "Odmenu dostane",
  "Odmenu navrhl", "Mesic/Rok proplaceni", "Skutecne vyplaceno dne", "Vyplaceno (priznak z Centraly)".
- **Cislo I nazev v lookupech** - data_set 195 a 197 vraci `id::text || ' - ' || nazev`
  (Peta chce videt oboji, jako ma Centrala: cislo v samostatnem policku + nazev).
- **Zaskrtavatka misto true/false** - comp_def 1288 (fix), 1289 (mesicne), 1294 (schvaleno)
  prepnuty z typu 2 (edit) na **107 (checkbox_modern)**; sloupce v PG jsou boolean.
  `vyplaceno` je v PG integer, proto zustava jako text.
- **Prehled (data_set 193)**: pridano Typ (cislo), Cislo dostane, Cislo navrhl, Platnost od, Platnost do.
- **Jadro zamknute na cteni** - `ec_pripl_srazky_actions.js`, `READ_ONLY = true`: pole disabled,
  tlacitko OK skryte, nahore oranzovy pruh "Jen ke cteni". Duvod stejny jako u vypnutych
  akcnich tlacitek (zive jednosmerne zrcadlo; zapis by prepsal dalsi sync a do mezd by nedosel).
  Commity 064683c1, eb7532e5.
- **Grid (vsechny moduly)**: `_looksLikePlainNumberName()` v `datagrid.js` - rok a osobni/typova
  cisla se zobrazuji bez oddelovace tisicu (drive "Rok 2026" -> "2 026"). Commit 2e2d737a.

## 4 gotchy frameworku (usetri hodiny)
1. **TECKA V NAZVU SLOUPCE = prazdne bunky.** Alias `AS "C. typu"` -> AG Grid bere tecku jako
   cestu do vnoreneho objektu (`row["C"]["typu"]`) -> hodnota undefined, bunka prazdna,
   ackoli API data vraci spravne. **V aliasech sloupcu nikdy nepouzivej tecku.**
2. **Ciselne stringy grid formatuje cs-CZ.** `inferColumnType` bere i string "2026" jako cislo
   -> "2 026". Cast na text tedy NEPOMUZE; resenim je valueFormatter (viz zmena vyse).
3. **Tlacitka OK / Storno nejsou v `.erp-modal-footer`**, ale v `.erp-design-grid` uvnitr dialogu.
   Kdo je hleda ve footeru, nenajde je.
4. **Diakritika pres SQL most bezpecne**: misto primeho zapisu ceskeho textu posilej
   `convert_from(decode('<base64>','base64'),'UTF8')`. Prenos je pak ciste ASCII, nic se
   neprekoduje. Overeno na 17 popiscich + 3 data_setech (27.7.), diakritika sedi.

## Co jsme zjistili k "pohledum pojisteni / tarif / kvalita"
- **tarif** = druhy odmeny 4 (Telefonni tarif do MZDY, 214 radku) a 43 (Telefonni tarif OSVC, 35).
- **kvalita** = druhy odmeny 30 a 31, ale **0 radku** v nasem dvouletem okne.
- **pojisteni** neni druh odmeny - je to jen text v poznamce. V Centrale 24 radku ve DVOU
  zneních: "Pojistka odpovednosti" (21x) a "Pojisteni odpovednosti pro EUROSOFT-Control" (3x).
  Petin filtr "pojisten" (Centrala porovnava bez diakritiky) vrati jen ty 3. U nas je PG ILIKE
  na diakritiku citlivy -> pohled musi pouzit unaccent nebo obe varianty.
- Framework na pohledy uz ma mechanismus: ulozene **sestavy** pod prehledem ("Ulozit jako...").
  Zadna zatim ulozena neni; ceka se na potvrzeni zadani od Petry.

## Otevrene (k 27.7.)
- Smer dat (zapis zpet do Centraly) - ceka na osobni rozhodnuti Marti Paska. Do te doby READ_ONLY.
- Nesrovnalost: na Petine snimku maji radky 18623 / 14640 / 11160 zaskrtnute Vyplaceno + datum,
  ale v `EC_FinPriplatkySrazkyDefinice` (i v zaloze DB_EC260531 z 31.5.) je `Vyplaceno=0` a
  `DatVyplaceni` NULL. Jeji grid navic ukazuje sloupec "Smlouva" (HPP/OSVC), ktery v te tabulce
  neni -> je to spojeny pohled. Neni vysvetleno, doptat se Petry.

