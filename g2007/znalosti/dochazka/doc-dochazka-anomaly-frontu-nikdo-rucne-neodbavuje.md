# Fronta chyb dochazky ve STRATEGII: 857 z 857 uzavrenych se zavrelo SAMO, rucne neodbavil nikdo (26. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> ## OPRAVA 26. 8. 2026 (tyz den, o dve hodiny pozdeji) - "0 rucne" UZ NEPLATI
>
> Mereno v 07:35, kdy `resolved_by IS NOT NULL` vracelo 0. **V 08:42 tehoz dne uzavrela
> Petra Safrankova (user 18) rucne nalez 1749866** (`prace_pri_absenci` u Michaely Hladikove).
> Cislo je tedy **1**, ne 0. Overil Claude-28 v 09:57 v zive databazi.
>
> **Co z puvodniho zaveru plati dal:** 1 z 858 porad znamena, ze se fronta prakticky neproklikava.
> **Co uz neplati:** tvrzeni "jeste NIKDY nikdo" - a nesmi se pouzivat jako argument, ze je
> hlidaci pravidlo zbytecne.
>
> **Podstatnejsi zjisteni: upozorneni PROKAZATELNE CHODI a lide podle nich zasahuji.**
> V `fw.mobile_command` jsou 26. 8. v 07:22 tri zpravy "Dochazka - nesrovnalost" (Petra Safrankova
> `done`, Michelle Safrankova `pending`, Michaela Hladikova `done`) - a prave Petra pak v 08:42
> ten nalez zavrela. Uzavreny retezec **hlidac -> notifikace -> clovek**. Stejne zpravy sly
> 25. 8. v 10:53 (Jakesova, Havlat, Hladikova) a od 24. 8. chodi i samotnemu cloveku
> (26. 8. v 05:00 Vojtech Purkar "Chybi dochazka 25.08.").
>
> Na zaklade toho bylo 26. 8. rozhodnuto pridat nove hlidaci pravidlo `dva_bezici_naraz` do
> `att_anomaly_scan` (v8), a NE do `tenant.pojistka` - viz
> [[doc-dochazka-duplicitni-bezici-zaznamy-dvoji-odeslani]].
>
> **NEOVERENO zustava** (upozornil uz autor): kdy do `tenant.att_anomaly` pribyl sloupec
> `resolved_by`. Kdyby pribyl pozdeji nez cast tech 857 uzaverek, mohl nekdo odbavovat rucne i driv.

# Frontu nalezenych chyb ve STRATEGII rucne neodbavuje nikdo

**Overeno 26. 8. 2026 v zive databazi a v zivem kodu. Nic nebylo zmeneno.**

## Cislo

| | Centrala | STRATEGIE |
|---|---|---|
| chyb celkem | — | **940** |
| uzavrenych | — | **857** |
| z toho automaticky (pricina zmizela) | — | **857 (vsechny)** |
| z toho rucne clovekem | Dusan 6 204 · Michelle 2 323 · Peta 2 494 · Kristyna 680 | **0** |
| otevrenych | — | **83** |

Dusan v Centrale odmavnul **1 344 chyb za poslednich 12 mesicu**, naposledy **22. 7. 2026 v 7.58** —
presne tehdy mu prestala chodit data (pichani se preneslo do STRATEGIE).

## Jak to bylo overeno

1. `SELECT count(*) FILTER (WHERE resolved_by IS NOT NULL) FROM tenant.att_anomaly` -> **0**
2. Kdo vubec umi chybu zavrit: `SELECT kod, position('resolved_by' in zdroj) FROM g2007.python
   WHERE zdroj ILIKE '%resolved_at=now()%' OR zdroj ILIKE '%SET resolved_at%'`
   -> **`att_fix_resolve` (v2) `resolved_by` MA**, **`att_anomaly_scan` (v7) NEMA**.
   Ostatni zasahy v tom vypisu (`app_vyroba_*`, `martinka_*`, `maminka_*`) jsou nad jinymi tabulkami.
3. Jadro aplikace `tenant.att_anomaly` jen **cte** (jediny vyskyt `resolved_at` je `SELECT count(*)`).

Tlacitko **"Hotovo - z fronty"** v Opravach dochazky (`att_fix_resolve`) tedy **funguje a zapisuje,
kdo ho zmackl** — jen ho zatim nikdo nepouzil.

## ⚠️ Co NENI overeno (dulezite, nez na tom nekdo postavi rozhodnuti)

**Neni overeno, kdy do `tenant.att_anomaly` pribyl sloupec `resolved_by`.** Kdyby pribyl pozdeji
nez cast tech 857 uzaverek, mohl v te starsi dobe nekdo odbavovat rucne a dnes to vypada jako
automat. **Tvrzeni spolehlive plati jen pro dobu, po kterou ten sloupec existuje.**

## Pozor na zamenu — "nikdo neodbavuje" NENI "nikdo se to nedozvi"

`att_anomaly_scan` se vola s `notify=True` a v hlavicce `att_neomluvena_absence` je popsano,
ze notifikace jde **editorum oprav dle pusobnosti** (vyroba = Misa a Dusan) a od **24. 8. 2026
i samotnemu cloveku** (rozhodla Peta, "lidem to zapni od ted dal").
⚠️ Cteno z popisu funkce, **NEOVERENO na odeslanych notifikacich**.

Rozdil je podstatny pri rozhodovani, jestli smi automat neco tise opravovat "s tim, ze hlidac
upozorni": hlidac muze upozornovat, i kdyz frontu nikdo neproklikava. **Kdo se na to pta
Marti-AI, musi ji dat obe casti** — ze fronta se neodbavuje i ze notifikace podle kodu existuji.
Jinak rozhoduje z pulky obrazku.

## Proc na tom zalezi

Prehled "Cely den - VV" se stavi prave proto, aby Dusan mel svou frontu chyb zpatky.
Kdyz uz dnes frontu ve STRATEGII nikdo neproklikava, je to signal, ze samotne zalozeni fronty
nestaci — musi se doresit, **jak se k ni clovek dostane a proc by do ni sahal**.

## Souvisi

- `doc-dochazka-anomaly-ciselnik-druhu-chyb-chybi` — druhy chyb a jejich pocty
- `doc-dochazka-centrala-nocni-kontrola-a-automaticke-opravy` — co kontrola sama opravi
- `doc-dochazka-prehled-cely-den-vv-centrala-rozbor` — nastroj, kvuli kteremu se to resi

