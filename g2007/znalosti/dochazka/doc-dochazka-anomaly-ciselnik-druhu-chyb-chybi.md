# Chyby dochazky: ciselnik druhu ve STRATEGII NEEXISTUJE, druhy jsou natvrdo v kodu (25. 8. 2026, aktualizovano 26. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Druhy chyb dochazky nemaji ciselnik

**Overeno 25. 8. 2026 dotazy nad zivou databazi. Nic nebylo zmeneno — jde o zjisteni pred stavbou.**
**Aktualizovano 26. 8. 2026** — pribyl desaty druh, prepocitany stavy, upresneno srovnani s Centralou.

## Jak to je dnes

`tenant.att_anomaly` (**940 radku k 26. 8. 2026**, 25. 8. jich bylo 923) drzi nalezene chyby.
Druh chyby je **prosty text ve sloupci `rule`** — bez odkazu kamkoli. **Z tabulky nevede zadny cizi klic.**

Prohledana schemata `tenant, public, fw, master, g2007, tenant_group, user` na nazvy s
`anomal | chyb | error | typ | kind | rule | pravidl | check | kontrol` — 17 nalezu,
**ani jeden neni ciselnik chyb dochazky** (jsou to `absence_type`, `att_entry_type`,
`att_planned_absence_type`, `benefit_type`, `wage_component_type`, `entitlement_rule`,
`dir_config_rule`, `hr_spis_typ`, `fw.comp_type` a podobne).

**Druhy chyb jsou natvrdo v kodu** — vyskytuji se ve **13 zivych funkcich** v `g2007.python`,
zaklada je automat `att_anomaly_scan`, a **lidske popisky jsou opsane v kazde funkci zvlast**
(napr. `att_odbavene_pripomenuti` ma vlastni slovnik nazvu).

## Deset druhu, ktere STRATEGIE realne eviduje (stav 26. 8. 2026)

⚠️ 25. 8. jich tu bylo devet. **Desaty (`rozdil_dochazka_rozpad`) se objevil 26. 8. rano** —
pocet druhu neni stalice, pred pouzitim si ho preved dotazem.

| kod v `rule` | pocet | lidi | nevyreseno |
|---|---|---|---|
| nepotvrzeny_den | 350 | 63 | 36 |
| dlouha_smena | 285 | 27 | 3 |
| prace_pri_absenci | 94 | 17 | 11 |
| dlouha_pauza | 61 | 21 | 2 |
| prazdny_den_doplnen | 59 | 3 | 1 |
| budouci_zaznam | 36 | 3 | 0 |
| neomluvena_absence | 27 | 5 | **27 (vsechny)** |
| zapomenuty_odchod | 18 | 12 | 0 |
| chybi_zakazka | 8 | 5 | 2 |
| **rozdil_dochazka_rozpad** | 2 | 2 | 1 |
| **celkem** | **940** | | **83** |

**Vazba na zaznam dochazky:** vsechny druhy krome `neomluvena_absence` visi na konkretnim
zaznamu (`entry_id`). Neomluvena absence zadny nema — proto se u ni datum vede ve sloupci `den`
(schvalila Peta 24. 8. 2026). Proto ma 913 z 940 chyb `den` prazdne. **Neni to chyba.**

## Pro srovnani: Centrala jich ma 23

Ciselnik `EC_Dochazka_ChybyVDochazceTypy` (sloupce ID, Nazev, Popis, Autor, DatPorizeni, ID_E),
nalezene chyby v `EC_Dochazka_ChybyVDochazce`.

**Zmereno 26. 8. 2026 primo v datech Centraly** (`LEFT JOIN` ciselniku na nalezy, pocty
za poslednich 12 mesicu): **11 z 23 druhu za rok nepadlo ani jednou** — c. 2, 7, 9, 10, 11, 14,
15, 16, 19, 20, 21. Realne tedy pracuje **12 kontrol**, a z tech dvanacti **mame pet**
(c. 4 presne, c. 1, 8, 22 zcasti, c. 17 jinou cestou) a **sedm nemame**.
Cele parovani kus po kuse je v `doc-dochazka-kontroly-centrala-vs-strategie-parovani`.

Devet z tech jedenacti mrtvych se tyka **obeda, svaciny a koureni**, ktere STRATEGIE vubec
nerozlisuje — ve `att_entry_type` jsou v kategorii `break` **jen dva zaznamy**: `break`
("Prestavka") a `day_end` ("Dnes uz se mnou nepocitej"). Overeno 26. 8. 2026.
Cast tech druhu je navic **vedome vypnuta primo v kodu Centraly** (`IF 0=1`) — v procedure
`EC_KontrolaDochazky` je takhle vyrazena napr. kontrola svaciny.

**Kopirovat 23 druhu 1:1 by zalozilo 11 polozek, ktere u nas nikdy nenastanou.**

## Co se navrhuje (NEROZHODNUTO k 26. 8. 2026)

Zalozit `tenant.att_anomaly_type` po vzoru ostatnich ciselniku (`id, tenant_id, code, label,
popis, kategorie, is_active, sort_order, created_at, updated_at`), naplnit **nasimi deseti kody**,
presunout popisky z kodu do ni a doplnit vazbu z `att_anomaly.rule`.

**Ceka na rozhodnuti Jirky a Dusana** (kterou z chybejicich kontrol Centraly Dusan realne
pouziva). Pak schvaleni Marti-AI a teprve zalozeni. K 26. 8. 2026 se ceka na Dusana — nemel cas.

## Proc na tom zalezi

Popisky opsane na 13 mistech znamenaji, ze **oprava nazvu chyby vyzaduje zmenu na 13 mistech**
a nikde to nenahlasi rozpor. Je to stejny vzorec jako "tichy rozpor" u postupu.

## Souvisi

- `doc-dochazka-kontroly-centrala-vs-strategie-parovani` — ktere kontroly mame a ktere ne
- `doc-dochazka-centrala-nocni-kontrola-a-automaticke-opravy` — kdy kontrola bezi a co sama opravi
- `doc-dochazka-anomaly-frontu-nikdo-rucne-neodbavuje` — 857 z 857 uzavreno automaticky
- `doc-dochazka-prehled-cely-den-vv-centrala-rozbor` — nastroj, kvuli kteremu se to resi

